const API_BASE_URL = "http://localhost:8000/api/calendar";

export interface CalendarEvent {
  id: string;
  user_id: string;
  title: string;
  start_time: string; // ISO format
  end_time: string; // ISO format
  event_type: string;
  location?: string;
  description?: string;
  color: string;
  recurrence: string;
  recurrence_end_date?: string | null;
  reminders: number[];
  duration_minutes?: number;
}

export interface EventCreateData {
  user_id: string;
  title: string;
  start_time: string;
  end_time: string;
  event_type: string;
  location?: string;
  description?: string;
  color?: string;
  recurrence?: string;
  recurrence_end_date?: string | null;
  reminders?: number[];
}

export interface EventUpdateData {
  title?: string;
  start_time?: string;
  end_time?: string;
  event_type?: string;
  location?: string;
  description?: string;
  color?: string;
  recurrence?: string;
  recurrence_end_date?: string | null;
  reminders?: number[];
}

export interface FreeSlot {
  start: string;
  end: string;
}

export interface FreeSlotsResponse {
  success: boolean;
  free_slots?: FreeSlot[];
  error?: string;
}

export interface StatisticsResponse {
  success: boolean;
  statistics?: {
    total_events: number;
    total_hours: number;
    average_duration_minutes: number;
    events_by_type: Record<string, number>;
  };
  error?: string;
}

/**
 * Get events for a user within a date range
 */
export async function getEvents(
  userId: string,
  start?: Date,
  end?: Date
): Promise<CalendarEvent[]> {
  // Guest mode: return a static sample calendar (read-only demo)
  if (userId === "guest") {
    // Simple sample events with different types and a recurring example
    const sample: CalendarEvent[] = [
      {
        id: "g1",
        user_id: "guest",
        title: "Class: Intro to Programming",
        start_time: new Date().toISOString().replace(/T.*$/, "T09:00:00.000Z"),
        end_time: new Date().toISOString().replace(/T.*$/, "T10:30:00.000Z"),
        event_type: "class",
        color: "#3498db",
        location: "Gainesville Hall 101",
        description: "Weekly lecture",
        recurrence: "weekly",
        recurrence_end_date: null,
        reminders: [15, 60]
      },
      {
        id: "g2",
        user_id: "guest",
        title: "Study Group",
        start_time: new Date().toISOString().replace(/T.*$/, "T12:00:00.000Z"),
        end_time: new Date().toISOString().replace(/T.*$/, "T13:00:00.000Z"),
        event_type: "study_group",
        color: "#2ecc71",
        location: "Library - Room B",
        description: "Weekly study session",
        recurrence: "weekly",
        recurrence_end_date: null,
        reminders: [15]
      },
      {
        id: "g3",
        user_id: "guest",
        title: "Exam Prep",
        start_time: new Date().toISOString().replace(/T.*$/, "T16:00:00.000Z"),
        end_time: new Date().toISOString().replace(/T.*$/, "T17:30:00.000Z"),
        event_type: "personal",
        color: "#9b59b6",
        location: "Study Room 12",
        description: "Prepare for upcoming midterm",
        recurrence: "none",
        recurrence_end_date: null,
        reminders: [60]
      }
    ];

    return Promise.resolve(sample);
  }
  const params = new URLSearchParams({ user_id: userId });
  if (start) {
    params.append("start", start.toISOString());
  }
  if (end) {
    params.append("end", end.toISOString());
  }

  const response = await fetch(`${API_BASE_URL}/events?${params.toString()}`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to fetch events" }));
    throw new Error(error.detail || "Failed to fetch events");
  }

  return response.json();
}

/**
 * Create a new calendar event
 */
export async function createEvent(eventData: EventCreateData): Promise<CalendarEvent> {
  // Disallow creating events in guest mode
  if (eventData.user_id === "guest") {
    throw new Error("Guest mode is read-only: cannot create events.");
  }
  const response = await fetch(`${API_BASE_URL}/events`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(eventData),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to create event" }));
    throw new Error(error.detail || "Failed to create event");
  }

  return response.json();
}

/**
 * Update an existing calendar event
 */
export async function updateEvent(
  eventId: string,
  userId: string,
  eventData: EventUpdateData
): Promise<void> {
  if (userId === "guest") {
    throw new Error("Guest mode is read-only: cannot update events.");
  }
  const params = new URLSearchParams({ user_id: userId });
  const response = await fetch(`${API_BASE_URL}/events/${eventId}?${params.toString()}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(eventData),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update event" }));
    throw new Error(error.detail || "Failed to update event");
  }
}

/**
 * Delete a calendar event
 */
export async function deleteEvent(
  eventId: string,
  userId: string,
  deleteFuture: boolean = false,
  fromDate?: Date
): Promise<void> {
  if (userId === "guest") {
    throw new Error("Guest mode is read-only: cannot delete events.");
  }
  const params = new URLSearchParams({ user_id: userId });
  if (deleteFuture) {
    params.append('delete_future', 'true');
    if (fromDate) params.append('from_date', fromDate.toISOString());
  }
  const response = await fetch(`${API_BASE_URL}/events/${eventId}?${params.toString()}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to delete event" }));
    throw new Error(error.detail || "Failed to delete event");
  }
}

/**
 * Find free time slots for a user
 */
export async function getFreeSlots(
  userId: string,
  start: Date,
  end: Date,
  minDuration: number = 30
): Promise<FreeSlotsResponse> {
  const params = new URLSearchParams({
    user_id: userId,
    start: start.toISOString(),
    end: end.toISOString(),
    min_duration: minDuration.toString(),
  });

  const response = await fetch(`${API_BASE_URL}/free-slots?${params.toString()}`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to find free slots" }));
    return { success: false, error: error.detail || "Failed to find free slots" };
  }

  return response.json();
}

/**
 * Get event statistics for a user
 */
export async function getStatistics(
  userId: string,
  start: Date,
  end: Date
): Promise<StatisticsResponse> {
  const params = new URLSearchParams({
    user_id: userId,
    start: start.toISOString(),
    end: end.toISOString(),
  });

  const response = await fetch(`${API_BASE_URL}/statistics?${params.toString()}`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to get statistics" }));
    return { success: false, error: error.detail || "Failed to get statistics" };
  }

  return response.json();
}

