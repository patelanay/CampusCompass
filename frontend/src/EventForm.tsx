import { useState, useEffect } from "react";
import { type CalendarEvent, type EventCreateData, type EventUpdateData, createEvent, updateEvent, deleteEvent } from "./api/calendarApi";
import { format } from "date-fns";

interface EventFormProps {
  event?: CalendarEvent | null;
  userId: string;
  startDate?: Date;
  onClose: () => void;
  onSave: () => void;
  readOnly?: boolean;
}

const EVENT_TYPES = [
  { value: "class", label: "Class" },
  { value: "exam", label: "Exam" },
  { value: "study_group", label: "Study Group" },
  { value: "office_hours", label: "Office Hours" },
  { value: "personal", label: "Personal" },
  { value: "meeting", label: "Meeting" },
  { value: "other", label: "Other" },
];

const RECURRENCE_TYPES = [
  { value: "none", label: "None" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "biweekly", label: "Biweekly" },
  { value: "monthly", label: "Monthly" },
];

const EVENT_TYPE_COLORS: Record<string, string> = {
  class: "#3498db",
  exam: "#e74c3c",
  study_group: "#2ecc71",
  office_hours: "#f39c12",
  personal: "#9b59b6",
  meeting: "#1abc9c",
  other: "#95a5a6",
};

export default function EventForm({ event, userId, startDate, onClose, onSave, readOnly = false }: EventFormProps) {
  const [title, setTitle] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [eventType, setEventType] = useState("class");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [recurrence, setRecurrence] = useState("none");
  const [recurrenceEndDate, setRecurrenceEndDate] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (event) {
      // Editing existing event
      setTitle(event.title);
      setStartTime(format(new Date(event.start_time), "yyyy-MM-dd'T'HH:mm"));
      setEndTime(format(new Date(event.end_time), "yyyy-MM-dd'T'HH:mm"));
      setEventType(event.event_type);
      setLocation(event.location || "");
      setDescription(event.description || "");
      setRecurrence(event.recurrence);
      setRecurrenceEndDate(
        event.recurrence_end_date ? format(new Date(event.recurrence_end_date), "yyyy-MM-dd'T'HH:mm") : ""
      );
    } else if (startDate) {
      // Creating new event - prefill with startDate
      const start = new Date(startDate);
      const end = new Date(startDate);
      end.setHours(end.getHours() + 1); // Default 1 hour duration
      setStartTime(format(start, "yyyy-MM-dd'T'HH:mm"));
      setEndTime(format(end, "yyyy-MM-dd'T'HH:mm"));
    }
  }, [event, startDate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
        if (readOnly) {
          setError("Guest mode is read-only: changes are not allowed.");
          setLoading(false);
          return;
        }
      const start = new Date(startTime);
      const end = new Date(endTime);

      if (start >= end) {
        setError("Start time must be before end time");
        setLoading(false);
        return;
      }

      if (!title.trim()) {
        setError("Title is required");
        setLoading(false);
        return;
      }

      if (event) {
        // Update existing event
        const updateData: EventUpdateData = {
          title,
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          event_type: eventType,
          location: location || undefined,
          description: description || undefined,
          color: EVENT_TYPE_COLORS[eventType],
          recurrence,
          recurrence_end_date: recurrence !== "none" && recurrenceEndDate ? new Date(recurrenceEndDate).toISOString() : null,
        };
        await updateEvent(event.id, userId, updateData);
      } else {
        // Create new event
        const createData: EventCreateData = {
          user_id: userId,
          title,
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          event_type: eventType,
          location: location || undefined,
          description: description || undefined,
          color: EVENT_TYPE_COLORS[eventType],
          recurrence,
          recurrence_end_date: recurrence !== "none" && recurrenceEndDate ? new Date(recurrenceEndDate).toISOString() : null,
          reminders: [15, 60],
        };
        await createEvent(createData);
      }

      onSave();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save event");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-[#003087]">
              {event ? "Edit Event" : "Create Event"}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
            >
              ×
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={readOnly}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003087]"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Time <span className="text-red-500">*</span>
                </label>
                <input
                  type="datetime-local"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  disabled={readOnly}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003087]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Time <span className="text-red-500">*</span>
                </label>
                <input
                  type="datetime-local"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  disabled={readOnly}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003087]"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Event Type <span className="text-red-500">*</span>
              </label>
              <select
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
                disabled={readOnly}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003087]"
              >
                {EVENT_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                disabled={readOnly}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003087]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={readOnly}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003087]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Recurrence</label>
              <select
                value={recurrence}
                onChange={(e) => setRecurrence(e.target.value)}
                disabled={readOnly}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003087]"
              >
                {RECURRENCE_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {recurrence !== "none" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Recurrence End Date
                </label>
                <input
                  type="datetime-local"
                  value={recurrenceEndDate}
                  onChange={(e) => setRecurrenceEndDate(e.target.value)}
                  disabled={readOnly}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#003087]"
                />
              </div>
            )}

            <div className="flex justify-between items-center gap-3 pt-4">
              {event && !readOnly && (
                <div className="flex gap-2 items-center">
                  <button
                    type="button"
                    onClick={async () => {
                      if (!event) return;
                      if (!confirm("Delete this event series? This will remove the event entirely.")) return;
                      setLoading(true);
                      try {
                        await deleteEvent(event.id, userId);
                        onSave();
                        onClose();
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "Failed to delete event");
                      } finally {
                        setLoading(false);
                      }
                    }}
                    className="px-3 py-1 border border-red-400 bg-red-50 text-red-700 rounded-md hover:bg-red-100"
                    disabled={loading}
                  >
                    Delete
                  </button>

                  {event.recurrence !== "none" && (
                    <button
                      type="button"
                      onClick={async () => {
                        if (!event) return;
                        const deleteFrom = new Date(event.start_time);
                        if (!confirm(`Delete this occurrence and all future occurrences starting from ${deleteFrom.toLocaleString()}?`)) return;
                        setLoading(true);
                        try {
                          await deleteEvent(event.id, userId, true, deleteFrom);
                          onSave();
                          onClose();
                        } catch (err) {
                          setError(err instanceof Error ? err.message : "Failed to delete event series from date");
                        } finally {
                          setLoading(false);
                        }
                      }}
                      className="px-3 py-1 border border-yellow-400 bg-yellow-50 text-yellow-700 rounded-md hover:bg-yellow-100"
                      disabled={loading}
                    >
                      Delete this & future
                    </button>
                  )}
                </div>
              )}
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                disabled={loading}
              >
                {readOnly ? "Close" : "Cancel"}
              </button>
              {!readOnly && (
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#003087] text-white rounded-md hover:bg-[#002366] disabled:opacity-50"
                  disabled={loading}
                >
                  {loading ? "Saving..." : "Save"}
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

