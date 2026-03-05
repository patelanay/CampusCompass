import unittest
from datetime import datetime, timezone

from backend.taskbar import Task, Taskbar


class TaskbarTests(unittest.TestCase):
    def test_task_to_dict_serializes_due_date_and_created_at(self):
        due_date = datetime(2026, 3, 10, 15, 0, tzinfo=timezone.utc)
        task = Task(title="Write tests", description="Coverage work", priority="high", due_date=due_date)
        task_dict = task.to_dict()

        self.assertEqual(task_dict["title"], "Write tests")
        self.assertEqual(task_dict["description"], "Coverage work")
        self.assertEqual(task_dict["priority"], "high")
        self.assertEqual(task_dict["due_date"], due_date.isoformat())
        self.assertTrue(task_dict["created_at"].endswith("+00:00"))

    def test_task_to_dict_without_due_date_has_none(self):
        task = Task(title="No due date")
        task_dict = task.to_dict()
        self.assertIsNone(task_dict["due_date"])

    def test_add_task_returns_id_and_stores_task(self):
        taskbar = Taskbar()
        task_id = taskbar.add_task("Build API", "Implement endpoints", "medium")

        self.assertIn(task_id, taskbar.tasks)
        self.assertEqual(taskbar.tasks[task_id].title, "Build API")

    def test_edit_task_updates_only_provided_fields(self):
        taskbar = Taskbar()
        task_id = taskbar.add_task("Old title", "Old desc", "low")
        success = taskbar.edit_task(task_id, {"title": "New title", "priority": "high"})

        self.assertTrue(success)
        self.assertEqual(taskbar.tasks[task_id].title, "New title")
        self.assertEqual(taskbar.tasks[task_id].priority, "high")
        self.assertEqual(taskbar.tasks[task_id].description, "Old desc")

    def test_edit_task_returns_false_for_missing_task(self):
        taskbar = Taskbar()
        self.assertFalse(taskbar.edit_task("missing-id", {"title": "x"}))

    def test_remove_task_success_and_failure(self):
        taskbar = Taskbar()
        task_id = taskbar.add_task("Task to remove")

        self.assertTrue(taskbar.remove_task(task_id))
        self.assertFalse(taskbar.remove_task(task_id))

    def test_list_tasks_returns_serialized_tasks(self):
        taskbar = Taskbar()
        taskbar.add_task("Task A")
        taskbar.add_task("Task B")
        tasks = taskbar.list_tasks()

        self.assertEqual(len(tasks), 2)
        self.assertEqual({task["title"] for task in tasks}, {"Task A", "Task B"})

    def test_mark_task_completed_success_and_failure(self):
        taskbar = Taskbar()
        task_id = taskbar.add_task("Complete me")

        self.assertTrue(taskbar.mark_task_completed(task_id))
        self.assertTrue(taskbar.tasks[task_id].completed)
        self.assertFalse(taskbar.mark_task_completed("missing-id"))


if __name__ == "__main__":
    unittest.main()
