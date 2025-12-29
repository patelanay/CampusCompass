import { useState, useEffect, useCallback } from "react";
import { Calendar as BigCalendar, momentLocalizer, type View, type SlotInfo } from "react-big-calendar";
import moment from "moment";
import "react-big-calendar/lib/css/react-big-calendar.css";
import "./css/calendar.css";
import { type CalendarEvent, getEvents } from "./api/calendarApi";
import EventForm from "./EventForm";
import { format } from "date-fns";

let localizer: ReturnType<typeof momentLocalizer>;
try {
  localizer = momentLocalizer(moment);
} catch (error) {
  console.error("Error initializing moment localizer:", error);
  // Fallback - this shouldn't happen but just in case
  localizer = momentLocalizer(moment);
}

interface CalendarProps {
  userId: string;
}

const EVENT_TYPE_COLORS: Record<string, string> = {
  class: "#3498db",
  exam: "#e74c3c",
  study_group: "#2ecc71",
  office_hours: "#f39c12",
  personal: "#9b59b6",
  meeting: "#1abc9c",
  other: "#95a5a6",
};

export default function Calendar({ userId }: CalendarProps) {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [currentView, setCurrentView] = useState<View>("month");
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [showEventForm, setShowEventForm] = useState(false);
  const [formStartDate, setFormStartDate] = useState<Date | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!userId) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Loading user information...</p>
      </div>
    );
  }

  // Calculate date range for fetching events based on current view
  const getDateRange = useCallback((date: Date, view: View): { start: Date; end: Date } => {
    const start = new Date(date);
    const end = new Date(date);

    switch (view) {
      case "month":
        start.setDate(1);
        start.setHours(0, 0, 0, 0);
        end.setMonth(end.getMonth() + 1);
        end.setDate(0);
        end.setHours(23, 59, 59, 999);
        break;
      case "week":
        const dayOfWeek = start.getDay();
        start.setDate(start.getDate() - dayOfWeek);
        start.setHours(0, 0, 0, 0);
        end.setDate(start.getDate() + 6);
        end.setHours(23, 59, 59, 999);
        break;
      case "day":
        start.setHours(0, 0, 0, 0);
        end.setHours(23, 59, 59, 999);
        break;
      default:
        start.setHours(0, 0, 0, 0);
        end.setHours(23, 59, 59, 999);
    }

    return { start, end };
  }, []);

  // Fetch events from API
  const fetchEvents = useCallback(async () => {
    if (!userId) {
      console.warn("Calendar: No userId provided");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const { start, end } = getDateRange(currentDate, currentView);
      const fetchedEvents = await getEvents(userId, start, end);
      setEvents(fetchedEvents || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load events";
      setError(errorMessage);
      console.error("Error fetching events:", err);
      // Don't throw - just show error message
    } finally {
      setLoading(false);
    }
  }, [userId, currentDate, currentView, getDateRange]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  // Convert CalendarEvent to react-big-calendar Event format
  const calendarEvents = events.map((event) => {
    try {
      return {
        id: event.id,
        title: event.title,
        start: new Date(event.start_time),
        end: new Date(event.end_time),
        resource: event,
      };
    } catch (err) {
      console.error("Error parsing event:", event, err);
      return null;
    }
  }).filter((e): e is NonNullable<typeof e> => e !== null);

  // Event style getter - color events based on type
  const eventStyleGetter = (event: any) => {
    const eventData = event.resource as CalendarEvent;
    const backgroundColor = eventData?.color || EVENT_TYPE_COLORS[eventData?.event_type] || "#3498db";
    const style = {
      backgroundColor,
      borderRadius: "5px",
      opacity: 0.8,
      color: "white",
      border: "0px",
      display: "block",
    };
    return { style };
  };

  // Handle event click
  const handleSelectEvent = (event: any) => {
    setSelectedEvent(event.resource as CalendarEvent);
    setShowEventForm(true);
  };

  // Handle slot selection (creating new event)
  const handleSelectSlot = (slotInfo: SlotInfo) => {
    setSelectedEvent(null);
    setFormStartDate(slotInfo.start);
    setShowEventForm(true);
  };

  // Handle event form save
  const handleEventSave = () => {
    fetchEvents();
    setShowEventForm(false);
    setSelectedEvent(null);
    setFormStartDate(undefined);
  };


  // Navigation handlers
  const handleNavigate = (date: Date) => {
    setCurrentDate(date);
  };

  const handleViewChange = (view: View) => {
    setCurrentView(view);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const goToPrevious = () => {
    const newDate = new Date(currentDate);
    if (currentView === "month") {
      newDate.setMonth(newDate.getMonth() - 1);
    } else if (currentView === "week") {
      newDate.setDate(newDate.getDate() - 7);
    } else {
      newDate.setDate(newDate.getDate() - 1);
    }
    setCurrentDate(newDate);
  };

  const goToNext = () => {
    const newDate = new Date(currentDate);
    if (currentView === "month") {
      newDate.setMonth(newDate.getMonth() + 1);
    } else if (currentView === "week") {
      newDate.setDate(newDate.getDate() + 7);
    } else {
      newDate.setDate(newDate.getDate() + 1);
    }
    setCurrentDate(newDate);
  };

  return (
    <div className="w-full h-full flex flex-col">
      {/* Calendar Controls */}
          <div className="bg-white p-4 border-b border-gray-200 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
          <button
            onClick={goToPrevious}
            className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50"
          >
            ←
          </button>
          <button
            onClick={goToToday}
            className="px-4 py-1 border border-gray-300 rounded hover:bg-gray-50"
          >
            Today
          </button>
          <button
            onClick={goToNext}
            className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50"
          >
            →
          </button>
          <h2 className="text-xl font-semibold text-[#003087] ml-4">
            {format(currentDate, currentView === "month" ? "MMMM yyyy" : currentView === "week" ? "MMM d, yyyy" : "EEEE, MMM d, yyyy")}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleViewChange("month")}
            className={`px-4 py-1 rounded ${
              currentView === "month"
                ? "bg-[#003087] text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Month
          </button>
          <button
            onClick={() => handleViewChange("week")}
            className={`px-4 py-1 rounded ${
              currentView === "week"
                ? "bg-[#003087] text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Week
          </button>
          <button
            onClick={() => handleViewChange("day")}
            className={`px-4 py-1 rounded ${
              currentView === "day"
                ? "bg-[#003087] text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Day
          </button>
          <button
            onClick={() => {
              setSelectedEvent(null);
              setFormStartDate(new Date());
              setShowEventForm(true);
            }}
            className="px-4 py-1 bg-[#FA4616] text-white rounded hover:bg-[#d93a0f] ml-2"
            style={{ display: userId === "demo" ? "none" : undefined }}
          >
            + New Event
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 mx-4 mt-4 rounded">
          {error}
        </div>
      )}

      {/* Calendar */}
      <div className="flex-1 bg-gray-50 overflow-hidden p-4">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500">Loading events...</p>
          </div>
        ) : (
          <div className="h-full w-full bg-white rounded-lg shadow-sm">
              <BigCalendar
              localizer={localizer}
              events={calendarEvents}
              startAccessor="start"
              endAccessor="end"
              style={{ height: "100%", width: "100%" }}
              view={currentView}
              onView={handleViewChange}
              date={currentDate}
              onNavigate={handleNavigate}
              onSelectEvent={handleSelectEvent}
              onSelectSlot={userId === "demo" ? undefined : handleSelectSlot}
              selectable={userId !== "guest"}
              eventPropGetter={eventStyleGetter}
              popup
            />
          </div>
        )}
      </div>

      {/* Event Form Modal */}
      {showEventForm && (
        <EventForm
          event={selectedEvent}
          userId={userId}
          readOnly={userId === "demo"}
          startDate={formStartDate}
          onClose={() => {
            setShowEventForm(false);
            setSelectedEvent(null);
            setFormStartDate(undefined);
          }}
          onSave={handleEventSave}
        />
      )}
    </div>
  );
}

