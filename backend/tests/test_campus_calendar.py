import unittest
from datetime import datetime, timezone

from backend.campus_calendar import InMemoryCalendarManager


def _event_payload(**overrides):
    payload = {
        "title": "Algorithms Lecture",
        "start_time": "2026-03-05T09:00:00Z",
        "end_time": "2026-03-05T10:00:00Z",
        "event_type": "class",
        "location": "CSE E220",
        "description": "Daily lecture",
        "color": "#2E6FEA",
        "recurrence": "none",
        "reminders": [15, 60],
    }
    payload.update(overrides)
    return payload


class InMemoryCalendarManagerTests(unittest.TestCase):
    def test_create_event_requires_all_required_fields(self):
        manager = InMemoryCalendarManager()
        result = manager.create_event("user-1", {"title": "Missing fields"})
        self.assertFalse(result["success"])
        self.assertIn("Missing field", result["error"])

    def test_create_event_rejects_invalid_datetime(self):
        manager = InMemoryCalendarManager()
        result = manager.create_event("user-1", _event_payload(start_time="not-a-date"))
        self.assertFalse(result["success"])
        self.assertIn("Invalid datetime format", result["error"])

    def test_create_event_rejects_reversed_time_range(self):
        manager = InMemoryCalendarManager()
        result = manager.create_event(
            "user-1",
            _event_payload(start_time="2026-03-05T11:00:00Z", end_time="2026-03-05T10:00:00Z"),
        )
        self.assertFalse(result["success"])
        self.assertIn("Start time must be before end time", result["error"])

    def test_create_event_success_and_get_event(self):
        manager = InMemoryCalendarManager()
        result = manager.create_event("user-1", _event_payload())
        self.assertTrue(result["success"])

        event = manager.get_event(result["event_id"], "user-1")
        self.assertIsNotNone(event)
        self.assertEqual(event["title"], "Algorithms Lecture")
        self.assertEqual(event["event_type"], "class")

    def test_create_event_detects_time_conflict(self):
        manager = InMemoryCalendarManager()
        first = manager.create_event("user-1", _event_payload())
        self.assertTrue(first["success"])

        second = manager.create_event(
            "user-1",
            _event_payload(start_time="2026-03-05T09:30:00Z", end_time="2026-03-05T10:30:00Z"),
        )
        self.assertFalse(second["success"])
        self.assertIn("conflicts", second["error"])

    def test_get_user_events_honors_date_filter(self):
        manager = InMemoryCalendarManager()
        manager.create_event(
            "user-1",
            _event_payload(title="Morning", start_time="2026-03-05T09:00:00Z", end_time="2026-03-05T10:00:00Z"),
        )
        manager.create_event(
            "user-1",
            _event_payload(title="Noon", start_time="2026-03-05T12:00:00Z", end_time="2026-03-05T13:00:00Z"),
        )

        filtered = manager.get_user_events(
            "user-1",
            start=datetime(2026, 3, 5, 10, 30, tzinfo=timezone.utc),
            end=datetime(2026, 3, 5, 13, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["title"], "Noon")

    def test_update_event_success_and_missing_event(self):
        manager = InMemoryCalendarManager()
        created = manager.create_event("user-1", _event_payload())
        event_id = created["event_id"]

        success = manager.update_event(event_id, "user-1", {"title": "Updated"})
        missing = manager.update_event("missing", "user-1", {"title": "Updated"})

        self.assertEqual(success, {"success": True})
        self.assertFalse(missing["success"])
        self.assertEqual(manager.get_event(event_id, "user-1")["title"], "Updated")

    def test_delete_event_success_and_failure(self):
        manager = InMemoryCalendarManager()
        created = manager.create_event("user-1", _event_payload())
        event_id = created["event_id"]

        self.assertEqual(manager.delete_event(event_id, "user-1"), {"success": True})
        missing = manager.delete_event(event_id, "user-1")
        self.assertFalse(missing["success"])

    def test_find_free_slots_returns_gaps(self):
        manager = InMemoryCalendarManager()
        manager.create_event("user-1", _event_payload(start_time="2026-03-05T09:00:00Z", end_time="2026-03-05T10:00:00Z"))
        manager.create_event("user-1", _event_payload(start_time="2026-03-05T11:00:00Z", end_time="2026-03-05T12:00:00Z"))

        free = manager.find_free_slots(
            "user-1",
            start=datetime(2026, 3, 5, 8, 0, tzinfo=timezone.utc),
            end=datetime(2026, 3, 5, 13, 0, tzinfo=timezone.utc),
            min_duration=30,
        )

        self.assertTrue(free["success"])
        self.assertEqual(len(free["free_slots"]), 3)
        self.assertTrue(free["free_slots"][0]["start"].startswith("2026-03-05T08:00:00"))

    def test_get_statistics_counts_event_types(self):
        manager = InMemoryCalendarManager()
        manager.create_event("user-1", _event_payload(event_type="class"))
        manager.create_event("user-1", _event_payload(event_type="exam", start_time="2026-03-05T11:00:00Z", end_time="2026-03-05T12:00:00Z"))

        stats = manager.get_statistics(
            "user-1",
            datetime(2026, 3, 5, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 6, 0, 0, tzinfo=timezone.utc),
        )

        self.assertTrue(stats["success"])
        self.assertEqual(stats["statistics"]["class"], 1)
        self.assertEqual(stats["statistics"]["exam"], 1)

    def test_load_user_calendar_check_availability(self):
        manager = InMemoryCalendarManager()
        manager.create_event("user-1", _event_payload(start_time="2026-03-05T09:00:00Z", end_time="2026-03-05T10:00:00Z"))
        calendar = manager.load_user_calendar("user-1")

        available = calendar.check_availability(
            datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 5, 11, 0, tzinfo=timezone.utc),
        )
        conflict = calendar.check_availability(
            datetime(2026, 3, 5, 9, 30, tzinfo=timezone.utc),
            datetime(2026, 3, 5, 9, 45, tzinfo=timezone.utc),
        )

        self.assertTrue(available)
        self.assertFalse(conflict)


if __name__ == "__main__":
    unittest.main()
