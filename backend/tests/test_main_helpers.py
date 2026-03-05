import unittest
from datetime import datetime, timezone

from fastapi import HTTPException

from backend import main


class MainHelpersTests(unittest.TestCase):
    def tearDown(self):
        main.user_taskbars.clear()

    def test_model_to_dict_supports_pydantic_models(self):
        payload = main.TaskCreate(user_id="user-1", title="Test task")
        serialized = main._model_to_dict(payload)
        self.assertEqual(serialized["user_id"], "user-1")
        self.assertEqual(serialized["title"], "Test task")

    def test_parse_iso_datetime_accepts_z_timezone(self):
        parsed = main._parse_iso_datetime("2026-03-05T10:00:00Z", "start")
        self.assertEqual(parsed.tzinfo, timezone.utc)
        self.assertEqual(parsed.hour, 10)

    def test_parse_iso_datetime_rejects_invalid_value(self):
        with self.assertRaises(HTTPException) as context:
            main._parse_iso_datetime("invalid", "start")
        self.assertEqual(context.exception.status_code, 422)

    def test_coerce_datetime_converts_naive_datetime_to_utc(self):
        parsed = main._coerce_datetime(datetime(2026, 3, 5, 10, 0), "start")
        self.assertEqual(parsed.tzinfo, timezone.utc)

    def test_coerce_datetime_rejects_unknown_type(self):
        with self.assertRaises(HTTPException) as context:
            main._coerce_datetime(1234, "start")
        self.assertEqual(context.exception.status_code, 422)

    def test_format_event_normalizes_datetime_and_defaults(self):
        event = {
            "_id": "event-1",
            "user_id": "user-1",
            "title": "Exam",
            "start_time": datetime(2026, 3, 5, 9, 0, tzinfo=timezone.utc),
            "end_time": datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc),
            "event_type": "exam",
            "recurrence_end_date": datetime(2026, 4, 1, 0, 0, tzinfo=timezone.utc),
        }

        formatted = main._format_event(event)
        self.assertEqual(formatted["id"], "event-1")
        self.assertTrue(formatted["start_time"].endswith("+00:00"))
        self.assertEqual(formatted["color"], "#3498db")
        self.assertEqual(formatted["recurrence"], "none")

    def test_require_calendar_manager_raises_when_unavailable(self):
        original = main.calendar_manager
        main.calendar_manager = None
        try:
            with self.assertRaises(HTTPException) as context:
                main._require_calendar_manager()
            self.assertEqual(context.exception.status_code, 503)
        finally:
            main.calendar_manager = original

    def test_get_or_create_taskbar_creates_and_reuses(self):
        first = main._get_or_create_taskbar("user-1")
        second = main._get_or_create_taskbar("user-1")
        self.assertIs(first, second)

    def test_get_existing_taskbar_raises_for_missing_user(self):
        with self.assertRaises(HTTPException) as context:
            main._get_existing_taskbar("missing-user")
        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
