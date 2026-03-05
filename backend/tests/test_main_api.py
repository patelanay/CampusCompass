import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException

from backend import main


def _event_payload(**overrides):
    payload = {
        "user_id": "user-1",
        "title": "Lecture",
        "start_time": "2026-03-05T09:00:00Z",
        "end_time": "2026-03-05T10:00:00Z",
        "event_type": "class",
        "location": "CSE E220",
        "description": "Lecture description",
        "color": "#2E6FEA",
        "recurrence": "none",
        "reminders": [15, 60],
    }
    payload.update(overrides)
    return payload


def _task_payload(**overrides):
    payload = {
        "user_id": "user-1",
        "title": "Do homework",
        "description": "Problem set",
        "priority": "medium",
    }
    payload.update(overrides)
    return payload


class MainApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        main.user_taskbars.clear()
        main.memory_db["calendars"].clear()
        main.mongo_client = None
        main.calendar_manager = main.InMemoryCalendarManager()

    async def asyncTearDown(self):
        main.user_taskbars.clear()
        main.memory_db["calendars"].clear()
        main.mongo_client = None
        main.calendar_manager = main.InMemoryCalendarManager()

    async def test_startup_event_falls_back_to_in_memory_calendar(self):
        with patch.object(main, "load_env_variables", return_value="mongodb://invalid"):
            with patch.object(main, "create_mongo_client", side_effect=RuntimeError("no mongo")):
                await main.startup_event()
        self.assertIsInstance(main.calendar_manager, main.InMemoryCalendarManager)

    async def test_shutdown_event_closes_mongo_client(self):
        class FakeMongoClient:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        fake_client = FakeMongoClient()
        main.mongo_client = fake_client
        await main.shutdown_event()
        self.assertTrue(fake_client.closed)

    async def test_calendars_roundtrip(self):
        created = main.add_calendar(main.Calendar(name="Spring Semester"))
        fetched = main.get_calendars()

        self.assertEqual(created.name, "Spring Semester")
        self.assertEqual(len(fetched["calendars"]), 1)
        self.assertEqual(fetched["calendars"][0].name, "Spring Semester")

    async def test_google_auth_success(self):
        with patch.object(main.id_token, "verify_oauth2_token", return_value={"email": "student@ufl.edu", "name": "UF Student", "sub": "user-123"}):
            result = await main.google_auth(main.GoogleAuthRequest(token="valid-token"))
        self.assertEqual(result.user_id, "user-123")
        self.assertEqual(result.user_email, "student@ufl.edu")

    async def test_google_auth_invalid_token_returns_401(self):
        with patch.object(main.id_token, "verify_oauth2_token", side_effect=ValueError("bad token")):
            with self.assertRaises(HTTPException) as context:
                await main.google_auth(main.GoogleAuthRequest(token="invalid-token"))
        self.assertEqual(context.exception.status_code, 401)

    async def test_calendar_endpoint_requires_manager(self):
        original = main.calendar_manager
        main.calendar_manager = None
        try:
            with self.assertRaises(HTTPException) as context:
                await main.get_events(user_id="user-1", start=None, end=None)
            self.assertEqual(context.exception.status_code, 503)
        finally:
            main.calendar_manager = original

    async def test_create_get_update_delete_calendar_event_flow(self):
        created = await main.create_event(main.EventCreate(**_event_payload()))
        event_id = created["id"]

        update = await main.update_event(
            event_id=event_id,
            event_data=main.EventUpdate(title="Updated Lecture"),
            user_id="user-1",
        )
        self.assertTrue(update["success"])

        events = await main.get_events(user_id="user-1", start=None, end=None)
        self.assertEqual(events[0]["title"], "Updated Lecture")

        deleted = await main.delete_event(event_id=event_id, user_id="user-1", delete_future=False, from_date=None)
        self.assertTrue(deleted["success"])

    async def test_create_event_rejects_invalid_time_range(self):
        payload = _event_payload(start_time="2026-03-05T11:00:00Z", end_time="2026-03-05T10:00:00Z")
        with self.assertRaises(HTTPException) as context:
            await main.create_event(main.EventCreate(**payload))
        self.assertEqual(context.exception.status_code, 422)

    async def test_create_event_rejects_invalid_recurrence_window(self):
        payload = _event_payload(recurrence="weekly", recurrence_end_date="2026-03-04T09:00:00Z")
        with self.assertRaises(HTTPException) as context:
            await main.create_event(main.EventCreate(**payload))
        self.assertEqual(context.exception.status_code, 422)

    async def test_update_event_requires_fields(self):
        created = await main.create_event(main.EventCreate(**_event_payload()))
        with self.assertRaises(HTTPException) as context:
            await main.update_event(event_id=created["id"], event_data=main.EventUpdate(), user_id="user-1")
        self.assertEqual(context.exception.status_code, 400)

    async def test_delete_event_not_found_returns_404(self):
        with self.assertRaises(HTTPException) as context:
            await main.delete_event(event_id="missing-id", user_id="user-1", delete_future=False, from_date=None)
        self.assertEqual(context.exception.status_code, 404)

    async def test_free_slots_rejects_invalid_window(self):
        with self.assertRaises(HTTPException) as context:
            await main.get_free_slots(
                user_id="user-1",
                start="2026-03-05T10:00:00Z",
                end="2026-03-05T10:00:00Z",
                min_duration=30,
            )
        self.assertEqual(context.exception.status_code, 422)

    async def test_statistics_returns_counts(self):
        await main.create_event(main.EventCreate(**_event_payload(event_type="class")))
        await main.create_event(
            main.EventCreate(
                **_event_payload(
                    event_type="exam",
                    start_time="2026-03-05T11:00:00Z",
                    end_time="2026-03-05T12:00:00Z",
                )
            )
        )

        response = await main.get_statistics(
            user_id="user-1",
            start="2026-03-05T00:00:00Z",
            end="2026-03-06T00:00:00Z",
        )

        self.assertTrue(response["success"])
        self.assertEqual(response["statistics"]["class"], 1)
        self.assertEqual(response["statistics"]["exam"], 1)

    async def test_create_task_rejects_blank_title_after_trim(self):
        with self.assertRaises(HTTPException) as context:
            await main.create_task(main.TaskCreate(**_task_payload(title="   ")))
        self.assertEqual(context.exception.status_code, 422)

    async def test_create_task_get_tasks_filter_sort_and_complete(self):
        low = await main.create_task(main.TaskCreate(**_task_payload(title="Low task", priority="low")))
        await main.create_task(main.TaskCreate(**_task_payload(title="Medium task", priority="medium")))
        high = await main.create_task(main.TaskCreate(**_task_payload(title="High task", priority="high")))

        sorted_tasks = await main.get_tasks(
            user_id="user-1",
            status="all",
            priority=None,
            sort_by="priority",
            sort_order="desc",
            limit=100,
            offset=0,
        )
        self.assertEqual(sorted_tasks[0].title, "High task")

        completed = await main.complete_task(task_id=high.id, user_id="user-1")
        self.assertTrue(completed.completed)

        pending_tasks = await main.get_tasks(
            user_id="user-1",
            status="pending",
            priority=None,
            sort_by="priority",
            sort_order="desc",
            limit=100,
            offset=0,
        )
        completed_tasks = await main.get_tasks(
            user_id="user-1",
            status="completed",
            priority=None,
            sort_by="priority",
            sort_order="desc",
            limit=100,
            offset=0,
        )

        self.assertTrue(all(task.completed is False for task in pending_tasks))
        self.assertTrue(all(task.completed is True for task in completed_tasks))
        self.assertEqual(low.priority.value, "low")

    async def test_get_tasks_due_date_sort_and_pagination(self):
        base = datetime(2026, 3, 5, 8, 0, tzinfo=timezone.utc)
        await main.create_task(main.TaskCreate(**_task_payload(title="Task 1", due_date=(base + timedelta(days=3)).isoformat())))
        await main.create_task(main.TaskCreate(**_task_payload(title="Task 2", due_date=(base + timedelta(days=1)).isoformat())))
        await main.create_task(main.TaskCreate(**_task_payload(title="Task 3")))

        tasks = await main.get_tasks(
            user_id="user-1",
            status="all",
            priority=None,
            sort_by="due_date",
            sort_order="asc",
            limit=2,
            offset=0,
        )

        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].title, "Task 2")
        self.assertEqual(tasks[1].title, "Task 1")

    async def test_update_task_not_found_returns_404(self):
        with self.assertRaises(HTTPException) as context:
            await main.update_task(task_id="missing", user_id="user-1", task_data=main.TaskUpdate(title="Updated"))
        self.assertEqual(context.exception.status_code, 404)

    async def test_update_task_rejects_blank_trimmed_title(self):
        created = await main.create_task(main.TaskCreate(**_task_payload(title="Original")))
        with self.assertRaises(HTTPException) as context:
            await main.update_task(task_id=created.id, user_id="user-1", task_data=main.TaskUpdate(title="    "))
        self.assertEqual(context.exception.status_code, 422)

    async def test_update_and_delete_task_flow(self):
        created = await main.create_task(main.TaskCreate(**_task_payload(title="Task to update")))
        updated = await main.update_task(
            task_id=created.id,
            user_id="user-1",
            task_data=main.TaskUpdate(title="Updated Task", priority="high", completed=True),
        )
        self.assertEqual(updated.title, "Updated Task")
        self.assertEqual(updated.priority.value, "high")
        self.assertTrue(updated.completed)

        deleted = await main.delete_task(task_id=created.id, user_id="user-1")
        self.assertTrue(deleted["success"])

    async def test_health_endpoint_returns_in_memory_counts(self):
        await main.create_task(main.TaskCreate(**_task_payload(title="Health check task")))
        payload = await main.health_check()

        self.assertEqual(payload.status, "ok")
        self.assertEqual(payload.calendar_backend, "in_memory")
        self.assertEqual(payload.users_with_taskbars, 1)
        self.assertEqual(payload.total_in_memory_tasks, 1)

    async def test_campus_map_endpoints(self):
        root = await main.get_campus_map()
        building = await main.get_building_map("cse")

        self.assertEqual(root["map_url"], "https://campusmap.ufl.edu/")
        self.assertIn("index/0042", building["map_url"])

    async def test_campus_map_building_not_found(self):
        with self.assertRaises(HTTPException) as context:
            await main.get_building_map("zzz")
        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
