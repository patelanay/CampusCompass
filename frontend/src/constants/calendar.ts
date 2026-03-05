export type EventType =
  | "class"
  | "exam"
  | "study_group"
  | "office_hours"
  | "personal"
  | "meeting"
  | "other";

export type RecurrenceType = "none" | "daily" | "weekly" | "biweekly" | "monthly";

export const EVENT_TYPES: Array<{ value: EventType; label: string }> = [
  { value: "class", label: "Class" },
  { value: "exam", label: "Exam" },
  { value: "study_group", label: "Study Group" },
  { value: "office_hours", label: "Office Hours" },
  { value: "personal", label: "Personal" },
  { value: "meeting", label: "Meeting" },
  { value: "other", label: "Other" },
];

export const RECURRENCE_TYPES: Array<{ value: RecurrenceType; label: string }> = [
  { value: "none", label: "None" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "biweekly", label: "Biweekly" },
  { value: "monthly", label: "Monthly" },
];

export const EVENT_TYPE_COLORS: Record<EventType, string> = {
  class: "#2E6FEA",
  exam: "#D74A2E",
  study_group: "#2EA07E",
  office_hours: "#F08A24",
  personal: "#6C63FF",
  meeting: "#1794B8",
  other: "#6B7280",
};

export const DEFAULT_EVENT_REMINDERS = [15, 60];
