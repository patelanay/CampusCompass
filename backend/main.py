import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone
from enum import Enum
import os
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests
from pymongo import MongoClient

try:
    from .calendar_manager import CalendarManager
    from .db_helpers import create_mongo_client, load_env_variables
    from .campus_calendar import InMemoryCalendarManager
    from .taskbar import Taskbar, Task
    from .uf_schedule import building_code_to_url
except ImportError:
    from calendar_manager import CalendarManager
    from db_helpers import create_mongo_client, load_env_variables
    from campus_calendar import InMemoryCalendarManager
    from taskbar import Taskbar, Task
    from uf_schedule import building_code_to_url

# Load environment variables
load_dotenv()

class Calendar(BaseModel):
    name: str

class Calendars(BaseModel):
    calendars: List[Calendar]

class GoogleAuthRequest(BaseModel):
    token: str

class AuthResponse(BaseModel):
    user_email: str
    user_name: str
    user_id: str

class PriorityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class RecurrenceType(str, Enum):
    none = "none"
    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"

class EventType(str, Enum):
    class_type = "class"
    exam = "exam"
    study_group = "study_group"
    office_hours = "office_hours"
    personal = "personal"
    meeting = "meeting"
    other = "other"

# Taskbar/Todo Models
class TaskCreate(BaseModel):
    user_id: str
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    priority: PriorityLevel = PriorityLevel.medium
    due_date: Optional[str] = None  # ISO format

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[PriorityLevel] = None
    due_date: Optional[str] = None
    completed: Optional[bool] = None

class TaskResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    priority: PriorityLevel
    due_date: Optional[str]
    completed: bool
    created_at: str

# Calendar Event Models
class EventCreate(BaseModel):
    user_id: str
    title: str = Field(min_length=1, max_length=200)
    start_time: str  # ISO format datetime string
    end_time: str    # ISO format datetime string
    event_type: EventType
    location: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = "#3498db"
    recurrence: RecurrenceType = RecurrenceType.none
    recurrence_end_date: Optional[str] = None
    reminders: List[int] = Field(default_factory=lambda: [15, 60])

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    event_type: Optional[EventType] = None
    location: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    recurrence: Optional[RecurrenceType] = None
    recurrence_end_date: Optional[str] = None
    reminders: Optional[List[int]] = None

class EventResponse(BaseModel):
    id: str
    user_id: str
    title: str
    start_time: str
    end_time: str
    event_type: str
    location: Optional[str] = None
    description: Optional[str] = None
    color: str
    recurrence: str
    recurrence_end_date: Optional[str] = None
    reminders: List[int]
    duration_minutes: Optional[int] = None

class HealthResponse(BaseModel):
    status: Literal["ok"]
    calendar_backend: Literal["mongodb", "in_memory", "unavailable"]
    mongo_connected: bool
    users_with_taskbars: int
    total_in_memory_tasks: int

app = FastAPI()

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# Initialize MongoDB and CalendarManager
mongo_client: Optional[MongoClient] = None
calendar_manager: Optional[CalendarManager] = None

# In-memory taskbars for each user (could be backed by MongoDB later)
user_taskbars: Dict[str, Taskbar] = {}

@app.on_event("startup")
async def startup_event():
    global mongo_client, calendar_manager
    try:
        uri = load_env_variables()
        mongo_client = create_mongo_client(uri)
        calendar_manager = CalendarManager(mongo_client)
        print("CalendarManager initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize MongoDB/CalendarManager: {e}")
        print("Falling back to in-memory calendar manager (no persistence).")
        # Use an in-memory fallback so the app remains functional for adding events during local dev
        try:
            calendar_manager = InMemoryCalendarManager()
            print("In-memory CalendarManager initialized successfully")
        except Exception as e2:
            print(f"Failed to initialize in-memory calendar manager: {e2}")
            print("Calendar features will not be available")

@app.on_event("shutdown")
async def shutdown_event():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("MongoDB connection closed")

origins = [
    "http://localhost:3000",
    "http://localhost:5173"  # Vite default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

memory_db = {"calendars":[]}
PRIORITY_RANK = {
    PriorityLevel.low.value: 1,
    PriorityLevel.medium.value: 2,
    PriorityLevel.high.value: 3
}

def _model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Compatibility helper for Pydantic v1/v2 model serialization."""
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()

def _parse_iso_datetime(value: str, field_name: str) -> datetime:
    """Parse ISO datetime and normalize to UTC-aware datetime."""
    try:
        cleaned = value.replace('Z', '+00:00') if 'Z' in value else value
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid ISO datetime for '{field_name}'")

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def _coerce_datetime(value: Any, field_name: str) -> datetime:
    """Accept datetime or ISO datetime string and return UTC-aware datetime."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        return _parse_iso_datetime(value, field_name)
    raise HTTPException(status_code=422, detail=f"Invalid datetime type for '{field_name}'")

def _format_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize an event document for API response shape."""
    recurrence_end = event.get('recurrence_end_date')
    recurrence_end_formatted = None
    if recurrence_end:
        recurrence_end_formatted = recurrence_end.isoformat() if isinstance(recurrence_end, datetime) else str(recurrence_end)

    return {
        'id': event.get('_id', event.get('id', '')),
        'user_id': event.get('user_id', ''),
        'title': event.get('title', ''),
        'start_time': event['start_time'].isoformat() if isinstance(event.get('start_time'), datetime) else str(event.get('start_time', '')),
        'end_time': event['end_time'].isoformat() if isinstance(event.get('end_time'), datetime) else str(event.get('end_time', '')),
        'event_type': event.get('event_type', ''),
        'location': event.get('location'),
        'description': event.get('description'),
        'color': event.get('color', '#3498db'),
        'recurrence': event.get('recurrence', 'none'),
        'recurrence_end_date': recurrence_end_formatted,
        'reminders': event.get('reminders', [15, 60])
    }


def _require_calendar_manager() -> Any:
    """Return a ready calendar manager or raise a service-unavailable error."""
    if not calendar_manager:
        raise HTTPException(status_code=503, detail="Calendar service unavailable")
    return calendar_manager


def _get_or_create_taskbar(user_id: str) -> Taskbar:
    """Return a taskbar for a user, creating one if needed."""
    if user_id not in user_taskbars:
        user_taskbars[user_id] = Taskbar()
    return user_taskbars[user_id]


def _get_existing_taskbar(user_id: str) -> Taskbar:
    """Return an existing taskbar or raise 404 when user has no taskbar."""
    if user_id not in user_taskbars:
        raise HTTPException(status_code=404, detail="User not found")
    return user_taskbars[user_id]


def _task_to_response(task: Task, user_id: str) -> TaskResponse:
    """Convert in-memory Task model to API response model."""
    return TaskResponse(
        id=task.id,
        user_id=user_id,
        title=task.title,
        description=task.description,
        priority=PriorityLevel(task.priority),
        due_date=task.due_date.isoformat() if task.due_date else None,
        completed=task.completed,
        created_at=task.created_at.isoformat(),
    )

@app.post("/api/auth/google", response_model=AuthResponse)
async def google_auth(auth_request: GoogleAuthRequest):
    try:
        # Verify the Google token
        idinfo = id_token.verify_oauth2_token(
            auth_request.token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )

        # Token is valid, extract user information
        user_email = idinfo.get("email")
        user_name = idinfo.get("name")
        user_id = idinfo.get("sub")

        # Optional: Restrict to UFL emails only
        # if not user_email.endswith("@ufl.edu"):
        #     raise HTTPException(status_code=403, detail="Only UFL email addresses are allowed")

        # Here you can also save/update user in your database
        # e.g., save user_id, user_email, user_name to MongoDB

        return AuthResponse(
            user_email=user_email,
            user_name=user_name,
            user_id=user_id
        )

    except ValueError as e:
        # Invalid token
        raise HTTPException(status_code=401, detail=f"Invalid authentication credentials: {str(e)}")

@app.get("/calendars", response_model=Calendars)
def get_calendars():
    # return the in-memory calendars list in the response model shape
    return {"calendars": memory_db["calendars"]}

@app.post("/calendars", response_model=Calendar)
def add_calendar(calendar: Calendar):
    memory_db["calendars"].append(calendar)
    return calendar

# Calendar API Endpoints
@app.get("/api/calendar/events", response_model=List[EventResponse])
async def get_events(
    user_id: str = Query(..., description="User ID"),
    start: Optional[str] = Query(None, description="Start date (ISO format)"),
    end: Optional[str] = Query(None, description="End date (ISO format)")
):
    """Get events for a user, optionally filtered by date range."""
    manager = _require_calendar_manager()
    
    try:
        start_dt = _parse_iso_datetime(start, "start") if start else None
        end_dt = _parse_iso_datetime(end, "end") if end else None

        if start_dt and end_dt and start_dt >= end_dt:
            raise HTTPException(status_code=422, detail="'start' must be before 'end'")
        
        events = manager.get_user_events(user_id, start_dt, end_dt)
        return [_format_event(event) for event in events]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching events: {str(e)}")

@app.post("/api/calendar/events", response_model=EventResponse)
async def create_event(event_data: EventCreate):
    """Create a new calendar event."""
    manager = _require_calendar_manager()
    
    try:
        start_dt = _parse_iso_datetime(event_data.start_time, "start_time")
        end_dt = _parse_iso_datetime(event_data.end_time, "end_time")
        if start_dt >= end_dt:
            raise HTTPException(status_code=422, detail="'start_time' must be before 'end_time'")

        if event_data.recurrence_end_date:
            recurrence_end_dt = _parse_iso_datetime(event_data.recurrence_end_date, "recurrence_end_date")
            if recurrence_end_dt < start_dt:
                raise HTTPException(status_code=422, detail="'recurrence_end_date' must be at or after 'start_time'")

        event_dict = _model_to_dict(event_data)
        result = manager.create_event(event_data.user_id, event_dict)
        
        if result['success']:
            # Fetch and return the created event
            event = manager.get_event(result['event_id'], event_data.user_id)
            if not event:
                raise HTTPException(status_code=500, detail="Event created but could not be retrieved")
            return _format_event(event)
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to create event'))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

@app.put("/api/calendar/events/{event_id}")
async def update_event(event_id: str, event_data: EventUpdate, user_id: str = Query(..., description="User ID")):
    """Update an existing calendar event."""
    manager = _require_calendar_manager()
    
    try:
        # Only include fields that are provided (not None)
        update_dict = {k: v for k, v in _model_to_dict(event_data).items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")

        existing_event = manager.get_event(event_id, user_id)
        if not existing_event:
            raise HTTPException(status_code=404, detail="Event not found")

        new_start = _coerce_datetime(update_dict.get('start_time', existing_event.get('start_time')), "start_time")
        new_end = _coerce_datetime(update_dict.get('end_time', existing_event.get('end_time')), "end_time")
        if new_start >= new_end:
            raise HTTPException(status_code=422, detail="'start_time' must be before 'end_time'")

        if 'recurrence_end_date' in update_dict and update_dict['recurrence_end_date'] is not None:
            recurrence_end_dt = _coerce_datetime(update_dict['recurrence_end_date'], "recurrence_end_date")
            if recurrence_end_dt < new_start:
                raise HTTPException(status_code=422, detail="'recurrence_end_date' must be at or after 'start_time'")
        
        result = manager.update_event(event_id, user_id, update_dict)
        
        if result['success']:
            return {"success": True}
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to update event'))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating event: {str(e)}")

@app.delete("/api/calendar/events/{event_id}")
async def delete_event(
    event_id: str,
    user_id: str = Query(..., description="User ID"),
    delete_future: bool = Query(False, description="If true, delete this event and future occurrences (for recurring events)"),
    from_date: Optional[str] = Query(None, description="ISO datetime to begin deleting future occurrences from; defaults to now")
):
    """Delete a calendar event."""
    manager = _require_calendar_manager()
    
    try:
        # Support deleting only future occurrences for recurring events
        parsed_from = None
        if delete_future:
            if from_date:
                parsed_from = _parse_iso_datetime(from_date, "from_date")
            else:
                parsed_from = datetime.now(timezone.utc)

        result = manager.delete_event(event_id, user_id, delete_future=delete_future, from_date=parsed_from)
        
        if result['success']:
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Event not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")

@app.get("/api/calendar/free-slots")
async def get_free_slots(
    user_id: str = Query(..., description="User ID"),
    start: str = Query(..., description="Start date (ISO format)"),
    end: str = Query(..., description="End date (ISO format)"),
    min_duration: int = Query(30, ge=1, le=1440, description="Minimum duration in minutes")
):
    """Find free time slots for a user in a date range."""
    manager = _require_calendar_manager()
    
    try:
        start_dt = _parse_iso_datetime(start, "start")
        end_dt = _parse_iso_datetime(end, "end")
        if start_dt >= end_dt:
            raise HTTPException(status_code=422, detail="'start' must be before 'end'")
        
        result = manager.find_free_slots(user_id, start_dt, end_dt, min_duration)
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to find free slots'))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding free slots: {str(e)}")

@app.get("/api/calendar/statistics")
async def get_statistics(
    user_id: str = Query(..., description="User ID"),
    start: str = Query(..., description="Start date (ISO format)"),
    end: str = Query(..., description="End date (ISO format)")
):
    """Get event statistics for a user in a date range."""
    manager = _require_calendar_manager()
    
    try:
        start_dt = _parse_iso_datetime(start, "start")
        end_dt = _parse_iso_datetime(end, "end")
        if start_dt >= end_dt:
            raise HTTPException(status_code=422, detail="'start' must be before 'end'")
        
        result = manager.get_statistics(user_id, start_dt, end_dt)
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to get statistics'))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

# ============================================================================
# Taskbar/Todo Endpoints
# ============================================================================

@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task_data: TaskCreate):
    """Create a new task."""
    try:
        user_id = task_data.user_id
        taskbar = _get_or_create_taskbar(user_id)
        task_title = task_data.title.strip()
        if not task_title:
            raise HTTPException(status_code=422, detail="Task title cannot be empty")

        due_date = None
        if task_data.due_date:
            due_date = _parse_iso_datetime(task_data.due_date, "due_date")

        task_id = taskbar.add_task(
            title=task_title,
            description=task_data.description,
            priority=task_data.priority.value,
            due_date=due_date
        )

        return _task_to_response(taskbar.tasks[task_id], user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@app.get("/api/tasks", response_model=List[TaskResponse])
async def get_tasks(
    user_id: str = Query(..., description="User ID"),
    status: Literal["all", "pending", "completed"] = Query("all", description="Filter by completion status"),
    priority: Optional[PriorityLevel] = Query(None, description="Filter by priority"),
    sort_by: Literal["created_at", "due_date", "priority"] = Query("priority", description="Sort field"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort order"),
    limit: int = Query(100, ge=1, le=500, description="Max number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip")
):
    """Get all tasks for a user."""
    try:
        taskbar = _get_or_create_taskbar(user_id)
        tasks = taskbar.list_tasks()

        if status == "pending":
            tasks = [task for task in tasks if not task['completed']]
        elif status == "completed":
            tasks = [task for task in tasks if task['completed']]

        if priority:
            tasks = [task for task in tasks if task['priority'] == priority.value]

        reverse = sort_order == "desc"
        if sort_by == "priority":
            tasks.sort(key=lambda task: PRIORITY_RANK.get(task.get('priority', 'medium'), 0), reverse=reverse)
        elif sort_by == "created_at":
            tasks.sort(key=lambda task: _parse_iso_datetime(task['created_at'], "created_at"), reverse=reverse)
        else:
            with_due_date = [task for task in tasks if task.get('due_date')]
            without_due_date = [task for task in tasks if not task.get('due_date')]
            with_due_date.sort(key=lambda task: _parse_iso_datetime(task['due_date'], "due_date"), reverse=reverse)
            tasks = with_due_date + without_due_date

        tasks = tasks[offset:offset + limit]

        return [
            TaskResponse(
                id=task_dict['id'],
                user_id=user_id,
                title=task_dict['title'],
                description=task_dict['description'],
                priority=PriorityLevel(task_dict['priority']),
                due_date=task_dict['due_date'],
                completed=task_dict['completed'],
                created_at=task_dict['created_at']
            )
            for task_dict in tasks
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")

@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, user_id: str = Query(..., description="User ID"), task_data: TaskUpdate = None):
    """Update a task."""
    try:
        taskbar = _get_existing_taskbar(user_id)
        update_dict = {}

        if task_data and task_data.title is not None:
            stripped_title = task_data.title.strip()
            if not stripped_title:
                raise HTTPException(status_code=422, detail="Task title cannot be empty")
            update_dict['title'] = stripped_title
        if task_data and task_data.description is not None:
            update_dict['description'] = task_data.description
        if task_data and task_data.priority is not None:
            update_dict['priority'] = task_data.priority.value
        if task_data and task_data.due_date is not None:
            update_dict['due_date'] = _parse_iso_datetime(task_data.due_date, "due_date")
        if task_data and task_data.completed is not None:
            update_dict['completed'] = task_data.completed

        success = taskbar.edit_task(task_id, update_dict)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return _task_to_response(taskbar.tasks[task_id], user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, user_id: str = Query(..., description="User ID")):
    """Delete a task."""
    try:
        taskbar = _get_existing_taskbar(user_id)
        success = taskbar.remove_task(task_id)

        if not success:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")

@app.post("/api/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: str, user_id: str = Query(..., description="User ID")):
    """Mark a task as completed."""
    try:
        taskbar = _get_existing_taskbar(user_id)
        success = taskbar.mark_task_completed(task_id)

        if not success:
            raise HTTPException(status_code=404, detail="Task not found")

        return _task_to_response(taskbar.tasks[task_id], user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing task: {str(e)}")

# ============================================================================
# Health Endpoint
# ============================================================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Basic health and in-memory workload snapshot."""
    if isinstance(calendar_manager, CalendarManager):
        calendar_backend = "mongodb"
    elif isinstance(calendar_manager, InMemoryCalendarManager):
        calendar_backend = "in_memory"
    else:
        calendar_backend = "unavailable"

    total_tasks = sum(len(taskbar.tasks) for taskbar in user_taskbars.values())

    return HealthResponse(
        status="ok",
        calendar_backend=calendar_backend,
        mongo_connected=mongo_client is not None,
        users_with_taskbars=len(user_taskbars),
        total_in_memory_tasks=total_tasks
    )

# ============================================================================
# Campus Map Endpoint
# ============================================================================

@app.get("/api/campus-map")
async def get_campus_map():
    """Get the main UF campus map URL."""
    return {"map_url": "https://campusmap.ufl.edu/"}

@app.get("/api/campus-map/building/{building_code}")
async def get_building_map(building_code: str):
    """Get the campus map URL for a specific building code."""
    building_code_upper = building_code.upper()
    if building_code_upper not in building_code_to_url:
        raise HTTPException(status_code=404, detail=f"Building code '{building_code}' not found")
    return {"map_url": building_code_to_url[building_code_upper]}

if __name__ == "__main__":
    uvicorn.run(app, host = "0.0.0.0", port = 8000)

#http://localhost:8000/docs
#http://localhost:8000/calendars
