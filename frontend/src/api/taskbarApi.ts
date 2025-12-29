const API_BASE_URL = "http://localhost:8000/api";

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  priority: "low" | "medium" | "high";
  due_date?: string;
  completed: boolean;
  created_at: string;
}

/**
 * Get all tasks for a user
 */
export async function getTasks(userId: string): Promise<Task[]> {
  if (userId === "guest") {
    // Return sample tasks for guest user
    return [
      {
        id: "sample-1",
        user_id: "guest",
        title: "Review Course Materials",
        description: "Complete the assigned reading for COP3502",
        priority: "high",
        due_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
        completed: false,
        created_at: new Date().toISOString(),
      },
      {
        id: "sample-2",
        user_id: "guest",
        title: "Project Deliverable",
        description: "Submit CEN3031 project components",
        priority: "high",
        due_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
        completed: false,
        created_at: new Date().toISOString(),
      },
      {
        id: "sample-3",
        user_id: "guest",
        title: "Lab Report",
        description: "Submit PHY2049 lab analysis",
        priority: "medium",
        due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        completed: false,
        created_at: new Date().toISOString(),
      },
    ];
  }

  const response = await fetch(`${API_BASE_URL}/tasks?user_id=${encodeURIComponent(userId)}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch tasks: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Create a new task
 */
export async function createTask(
  userId: string,
  title: string,
  description?: string,
  priority: "low" | "medium" | "high" = "medium",
  due_date?: string
): Promise<Task> {
  if (userId === "guest") {
    throw new Error("Guest users cannot create tasks");
  }

  const response = await fetch(`${API_BASE_URL}/tasks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      title,
      description,
      priority,
      due_date,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create task: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update an existing task
 */
export async function updateTask(
  userId: string,
  taskId: string,
  updates: Partial<Omit<Task, "id" | "user_id" | "created_at">>
): Promise<Task> {
  if (userId === "guest") {
    throw new Error("Guest users cannot update tasks");
  }

  const response = await fetch(`${API_BASE_URL}/tasks/${encodeURIComponent(taskId)}?user_id=${encodeURIComponent(userId)}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error(`Failed to update task: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Mark a task as completed
 */
export async function completeTask(userId: string, taskId: string): Promise<Task> {
  if (userId === "guest") {
    throw new Error("Guest users cannot complete tasks");
  }

  const response = await fetch(`${API_BASE_URL}/tasks/${encodeURIComponent(taskId)}/complete?user_id=${encodeURIComponent(userId)}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to complete task: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Delete a task
 */
export async function deleteTask(userId: string, taskId: string): Promise<void> {
  if (userId === "guest") {
    throw new Error("Guest users cannot delete tasks");
  }

  const response = await fetch(`${API_BASE_URL}/tasks/${encodeURIComponent(taskId)}?user_id=${encodeURIComponent(userId)}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`Failed to delete task: ${response.statusText}`);
  }
}
