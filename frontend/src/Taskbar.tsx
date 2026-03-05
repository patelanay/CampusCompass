import { useEffect, useState } from "react";
import type { Task } from "./api/taskbarApi";
import { getTasks, createTask, updateTask, deleteTask } from "./api/taskbarApi";

interface TaskbarProps {
  userId: string;
}

const Taskbar = ({ userId }: TaskbarProps) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskDescription, setNewTaskDescription] = useState("");
  const [newTaskPriority, setNewTaskPriority] = useState<"low" | "medium" | "high">("medium");
  const [filter, setFilter] = useState<"all" | "pending" | "completed">("all");
  const isGuest = userId === "guest";

  // Load tasks on component mount
  useEffect(() => {
    loadTasks();
  }, [userId]);

  const loadTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedTasks = await getTasks(userId);
      setTasks(fetchedTasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  };

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    try {
      const newTask = await createTask(
        userId,
        newTaskTitle,
        newTaskDescription || undefined,
        newTaskPriority
      );
      setTasks([...tasks, newTask]);
      setNewTaskTitle("");
      setNewTaskDescription("");
      setNewTaskPriority("medium");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    }
  };

  const handleToggleTask = async (taskId: string, currentCompleted: boolean) => {
    try {
      const updatedTask = await updateTask(userId, taskId, { completed: !currentCompleted });
      setTasks(tasks.map((t) => (t.id === taskId ? updatedTask : t)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle task");
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    try {
      await deleteTask(userId, taskId);
      setTasks(tasks.filter((t) => t.id !== taskId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete task");
    }
  };

  const filteredTasks = tasks.filter((task) => {
    if (filter === "pending") return !task.completed;
    if (filter === "completed") return task.completed;
    return true;
  });

  // Sort tasks by priority (high > medium > low)
  const priorityOrder = { high: 0, medium: 1, low: 2 };
  const sortedFilteredTasks = [...filteredTasks].sort((a, b) => {
    const priorityA = priorityOrder[a.priority as keyof typeof priorityOrder] ?? 3;
    const priorityB = priorityOrder[b.priority as keyof typeof priorityOrder] ?? 3;
    return priorityA - priorityB;
  });

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "text-red-600 bg-red-50";
      case "medium":
        return "text-yellow-600 bg-yellow-50";
      case "low":
        return "text-green-600 bg-green-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const formatDueDate = (dateString?: string) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  return (
    <div className="h-full max-w-md bg-white border-l border-gray-200 flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 text-white px-6 py-4">
        <h2 className="text-xl font-bold">Tasks</h2>
      </div>

      {/* Filter tabs */}
      <div className="flex border-b border-gray-200 px-6 pt-4">
        {["all", "pending", "completed"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f as typeof filter)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition ${
              filter === f
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Error message */}
      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Task list */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
        {loading ? (
          <div className="text-center text-gray-500">Loading tasks...</div>
        ) : filteredTasks.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            {filter === "all"
              ? "No tasks yet. Create one to get started!"
              : `No ${filter} tasks`}
          </div>
        ) : (
          sortedFilteredTasks.map((task) => (
            <div
              key={task.id}
              className={`p-3 border border-gray-200 rounded-lg hover:shadow-md transition ${
                task.completed ? "bg-gray-50" : "bg-white"
              }`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={task.completed}
                  onChange={() => handleToggleTask(task.id, task.completed)}
                  disabled={isGuest}
                  className="mt-1 w-5 h-5 text-indigo-600 rounded cursor-pointer disabled:opacity-50"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p
                      className={`font-medium text-sm ${
                        task.completed ? "line-through text-gray-400" : "text-gray-900"
                      }`}
                    >
                      {task.title}
                    </p>
                    <span className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap flex-shrink-0 ${getPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                  </div>
                  {task.description && (
                    <p className="text-xs text-gray-600 mt-1 line-clamp-2">{task.description}</p>
                  )}
                  {task.due_date && (
                    <p className="text-xs text-gray-500 mt-2">Due: {formatDueDate(task.due_date)}</p>
                  )}
                </div>
                <button
                  onClick={() => handleDeleteTask(task.id)}
                  disabled={isGuest}
                  className="text-gray-400 hover:text-red-600 disabled:opacity-50 flex-shrink-0"
                  title="Delete task"
                >
                  ✕
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add new task form */}
      {!isGuest && (
        <form onSubmit={handleAddTask} className="border-t border-gray-200 bg-gray-50 p-4">
          <div className="space-y-2">
            <input
              type="text"
              placeholder="Add a new task..."
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
            />
            <textarea
              placeholder="Description (optional)"
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none"
              rows={2}
            />
            <select
              value={newTaskPriority}
              onChange={(e) => setNewTaskPriority(e.target.value as "low" | "medium" | "high")}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
            >
              <option value="low">Low Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="high">High Priority</option>
            </select>
            <button
              type="submit"
              className="w-full px-4 py-2 bg-indigo-600 text-white rounded text-sm font-medium hover:bg-indigo-700 transition"
            >
              Add Task
            </button>
          </div>
        </form>
      )}

      {isGuest && (
        <div className="border-t border-gray-200 bg-blue-50 p-4 text-xs text-blue-700">
          💡 Guest users can view tasks in read-only mode. Sign in to create and manage your own tasks.
        </div>
      )}
    </div>
  );
};

export default Taskbar;
