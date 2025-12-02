"""
Calendar Module for CampusCompass Backend

This module provides a complete calendar system with:
- Event management (CRUD operations)
- Recurrence pattern handling (daily, weekly, monthly, etc.)
- Availability checking and free slot finding
- MongoDB persistence
- Business logic for event creation and conflict detection

Architecture:
  - CalendarEvent: Data class for individual events
  - Calendar: In-memory calendar logic (recurrence, availability, stats)
  - CalendarManager: Bridges in-memory logic with MongoDB persistence
  
Usage:
  manager = CalendarManager(mongo_client)
  event_id = manager.create_event(user_id, event_data)
  free_slots = manager.find_free_slots(user_id, start, end)
"""

from datetime import datetime, timedelta, time, timezone
from enum import Enum
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId
import uuid


# ============================================================================
# Enums for Event Types and Recurrence
# ============================================================================

class EventType(Enum):
    """Available event types."""
    CLASS = "class"
    EXAM = "exam"
    STUDY_GROUP = "study_group"
    OFFICE_HOURS = "office_hours"
    PERSONAL = "personal"
    MEETING = "meeting"
    OTHER = "other"


class RecurrenceType(Enum):
    """Available recurrence patterns."""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CalendarEvent:
    """
    Represents a calendar event (with optional recurrence).
    
    Attributes:
        id: Unique event identifier (MongoDB ObjectId as string)
        user_id: User who owns the event
        title: Event name
        start_time: When the event begins (datetime)
        end_time: When the event ends (datetime)
        event_type: Type of event (class, exam, etc.)
        location: Where the event is (optional)
        description: Additional details (optional)
        color: Hex color for UI display (default: blue)
        recurrence: How often this repeats (none, daily, weekly, etc.)
        recurrence_end_date: When recurring stops (optional)
        reminders: List of minutes before event to remind (e.g., [15, 60])
    """
    id: str
    user_id: str
    title: str
    start_time: datetime
    end_time: datetime
    event_type: str
    location: Optional[str] = None
    description: Optional[str] = None
    color: str = "#3498db"
    recurrence: str = "none"
    recurrence_end_date: Optional[datetime] = None
    reminders: List[int] = None
    
    def __post_init__(self):
        """Validate event on creation."""
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")
        if self.reminders is None:
            self.reminders = [15, 60]
    
    def duration_minutes(self) -> int:
        """Calculate event duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary for JSON/DB storage."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'event_type': self.event_type,
            'location': self.location,
            'description': self.description,
            'color': self.color,
            'recurrence': self.recurrence,
            'recurrence_end_date': self.recurrence_end_date.isoformat() if self.recurrence_end_date else None,
            'reminders': self.reminders,
            'duration_minutes': self.duration_minutes()
        }


# ============================================================================
# Calendar Logic (In-Memory)
# ============================================================================

class Calendar:
    """
    In-memory calendar for a user.
    Handles all non-database logic:
    - Recurring event expansion
    - Free slot finding
    - Availability checking
    - Statistics
    """
    
    def __init__(self, user_id: str):
        """Initialize calendar for a user."""
        self.user_id = user_id
        self.events: Dict[str, CalendarEvent] = {}

    def _ensure_aware(self, dt: datetime) -> datetime:
        """Ensure datetime is timezone-aware (UTC)."""
        if dt is None:
            return dt
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    
    def add_event(self, event: CalendarEvent) -> None:
        """Add an event to the calendar."""
        self.events[event.id] = event
    
    def remove_event(self, event_id: str) -> bool:
        """Remove an event. Returns True if removed, False if not found."""
        if event_id in self.events:
            del self.events[event_id]
            return True
        return False
    
    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """Get a specific event by ID."""
        return self.events.get(event_id)
    
    def expand_recurring_event(self, event: CalendarEvent, start: datetime, 
                              end: datetime) -> List[Tuple[datetime, datetime]]:
        """
        Generate all instances of a recurring event within a date range.
        
        Example:
          Event: "Daily standup" at 9 AM every day
          Result: List of (9 AM Mon, 9 AM Tue, 9 AM Wed, ...)
        
        Args:
            event: The recurring event
            start: Start of search range
            end: End of search range
        
        Returns:
            List of (start_time, end_time) tuples for each instance
        """
        # Normalize inputs to timezone-aware UTC
        start = self._ensure_aware(start)
        end = self._ensure_aware(end)

        if event.recurrence == "none":
            # Single event - return if it falls in range
            ev_start = self._ensure_aware(event.start_time)
            if start <= ev_start < end:
                return [(event.start_time, event.end_time)]
            return []
        
        instances = []
        current = self._ensure_aware(event.start_time)
        duration = event.end_time - event.start_time
        limit = self._ensure_aware(event.recurrence_end_date) if event.recurrence_end_date else end
        
        while current < limit and current < end:
            if current >= start:
                instances.append((current, current + duration))
            
            # Move to next occurrence based on recurrence type
            if event.recurrence == "daily":
                current += timedelta(days=1)
            elif event.recurrence == "weekly":
                current += timedelta(weeks=1)
            elif event.recurrence == "biweekly":
                current += timedelta(weeks=2)
            elif event.recurrence == "monthly":
                # Handle month boundaries correctly
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
        
        return instances
    
    def get_events_for_range(self, start: datetime, end: datetime) -> List[Tuple[datetime, datetime, CalendarEvent]]:
        """
        Get all event instances (with recurrence expanded) for a date range.
        
        Returns:
            List of (start_time, end_time, original_event) tuples, sorted by time
        """
        # Normalize inputs
        start = self._ensure_aware(start)
        end = self._ensure_aware(end)

        instances = []
        
        for event in self.events.values():
            # Expand recurring events
            times = self.expand_recurring_event(event, start, end)
            for event_start, event_end in times:
                instances.append((event_start, event_end, event))
        
        # Sort by start time
        instances.sort(key=lambda x: x[0])
        return instances
    
    def check_availability(self, start: datetime, end: datetime) -> bool:
        """
        Check if a time slot is free (no conflicts).
        
        Args:
            start: Start of requested time
            end: End of requested time
        
        Returns:
            True if available, False if there's a conflict
        """
        # Normalize inputs
        start = self._ensure_aware(start)
        end = self._ensure_aware(end)

        events = self.get_events_for_range(start, end)
        for event_start, event_end, _ in events:
            # Check if times overlap: start1 < end2 AND end1 > start2
            if start < event_end and end > event_start:
                return False
        return True
    
    def find_free_slots(self, start_date: datetime, end_date: datetime,
                       min_duration: int = 30,
                       work_start: time = time(8, 0),
                       work_end: time = time(22, 0)) -> List[Tuple[datetime, datetime]]:
        """
        Find all free time slots within a date range.
        
        Example:
          User has class 9-10 AM and 2-3 PM today
          Result: [(8:00, 9:00), (10:00, 14:00), (15:00, 22:00)]
        
        Args:
            start_date: Start of search range
            end_date: End of search range
            min_duration: Minimum slot duration in minutes
            work_start: Start of working hours (default 8 AM)
            work_end: End of working hours (default 10 PM)
        
        Returns:
            List of (start, end) tuples for free slots
        """
        free_slots = []
        # ensure aware
        current = self._ensure_aware(start_date)
        end_date = self._ensure_aware(end_date)
        
        while current.date() < end_date.date():
            # Define today's working hours
            # preserve timezone info when combining dates/times
            tz = current.tzinfo if current.tzinfo else timezone.utc
            day_start = datetime.combine(current.date(), work_start).replace(tzinfo=tz)
            day_end = datetime.combine(current.date(), work_end).replace(tzinfo=tz)
            
            # Get all busy times today
            busy = sorted(
                self.get_events_for_range(day_start, day_end),
                key=lambda x: x[0]
            )
            
            # Find gaps between busy slots
            slot_start = day_start
            for busy_start, busy_end, _ in busy:
                # Is there a gap before this busy event?
                if busy_start > slot_start:
                    gap_duration = (busy_start - slot_start).total_seconds() / 60
                    if gap_duration >= min_duration:
                        free_slots.append((slot_start, busy_start))
                
                slot_start = busy_end
            
            # Check for free time after last event
            if slot_start < day_end:
                gap_duration = (day_end - slot_start).total_seconds() / 60
                if gap_duration >= min_duration:
                    free_slots.append((slot_start, day_end))
            
            current = current + timedelta(days=1)
        
        return free_slots
    
    def find_first_available_slot(self, duration_minutes: int, start: datetime,
                                 end: datetime, work_start: time = time(8, 0),
                                 work_end: time = time(22, 0)) -> Optional[Tuple[datetime, datetime]]:
        """
        Find the first available time slot of requested duration.
        
        Args:
            duration_minutes: How long you need
            start: Start searching from this date
            end: Stop searching at this date
            work_start/work_end: Working hour boundaries
        
        Returns:
            (start_time, end_time) tuple or None if not found
        """
        # Make sure start/end are timezone-aware
        start = self._ensure_aware(start)
        end = self._ensure_aware(end)

        free_slots = self.find_free_slots(start, end, duration_minutes, work_start, work_end)
        if free_slots:
            slot_start, _ = free_slots[0]
            return (slot_start, slot_start + timedelta(minutes=duration_minutes))
        return None
    
    def get_statistics(self, start: datetime, end: datetime) -> Dict:
        """
        Get summary stats for a date range.
        
        Returns:
            Dict with total_events, total_hours, average_duration, events_by_type
        """
        # normalize
        start = self._ensure_aware(start)
        end = self._ensure_aware(end)

        instances = self.get_events_for_range(start, end)
        
        if not instances:
            return {
                'total_events': 0,
                'total_hours': 0,
                'average_duration': 0,
                'events_by_type': {}
            }
        
        # Count by type and calculate hours
        type_counts = {}
        total_minutes = 0
        
        for start_time, end_time, event in instances:
            duration = (end_time - start_time).total_seconds() / 60
            total_minutes += duration
            
            event_type = event.event_type
            if event_type not in type_counts:
                type_counts[event_type] = 0
            type_counts[event_type] += 1
        
        avg_duration = total_minutes / len(instances) if instances else 0
        
        return {
            'total_events': len(instances),
            'total_hours': round(total_minutes / 60, 2),
            'average_duration_minutes': round(avg_duration, 0),
            'events_by_type': type_counts
        }


# ============================================================================
# Database Manager (MongoDB)
# ============================================================================

class CalendarManager:
    """
    Manages calendar events: persistence + business logic.
    Combines MongoDB operations with in-memory Calendar logic.
    
    This is the main class to use - it handles everything:
    - Creating/updating/deleting events with conflict checking
    - Loading calendars from MongoDB
    - Finding free slots
    - Calculating statistics
    """
    
    def __init__(self, mongo_client: MongoClient, db_name: str = "campuscompass"):
        """
        Initialize calendar manager.
        
        Args:
            mongo_client: Connected MongoDB client
            db_name: Database name (default: campuscompass)
        """
        self.client = mongo_client
        self.db = mongo_client[db_name]
        self.collection = self.db["calendar_events"]
        
        # Create indexes for fast queries by user and date
        self.collection.create_index([("user_id", 1), ("start_time", 1)])
        self.collection.create_index([("user_id", 1), ("end_time", 1)])
    
    @staticmethod
    def _parse_datetime(dt_input) -> datetime:
        """
        Parse datetime from multiple formats.
        
        Handles: datetime objects, ISO strings, common date strings
        Useful for accepting user input in various formats.
        """
        # Return timezone-aware datetimes (normalize to UTC).
        if isinstance(dt_input, datetime):
            # If the datetime is naive, assume UTC. If it has tzinfo, convert to UTC.
            if dt_input.tzinfo is None:
                return dt_input.replace(tzinfo=timezone.utc)
            return dt_input.astimezone(timezone.utc)
        
        if isinstance(dt_input, str):
            # Try ISO format first (2023-11-13T10:30:00)
            try:
                dt = datetime.fromisoformat(dt_input.replace('Z', '+00:00'))
                # Ensure timezone-aware (normalize to UTC)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt
            except ValueError:
                pass
            
            # Try other common formats
            formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y']
            for fmt in formats:
                try:
                    dt = datetime.strptime(dt_input, fmt)
                    # parsed naive -> assume UTC
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            
            raise ValueError(f"Cannot parse datetime: {dt_input}")
        
        raise TypeError(f"Cannot parse {type(dt_input)} as datetime")
    
    def create_event(self, user_id: str, event_data: Dict) -> Dict:
        """
        Create a new event (with conflict checking).
        
        Flow:
        1. Validate required fields
        2. Load user's calendar to check conflicts
        3. If no conflict, save to MongoDB
        4. Return event_id and success status
        
        Args:
            user_id: User creating the event
            event_data: Dict with title, start_time, end_time, event_type, etc.
        
        Returns:
            {success: bool, event_id: str, error: str or None}
        """
        try:
            # Validate required fields
            required = ['title', 'start_time', 'end_time', 'event_type']
            for field in required:
                if field not in event_data:
                    return {'success': False, 'error': f"Missing field: {field}"}
            
            # Parse times
            start_time = self._parse_datetime(event_data['start_time'])
            end_time = self._parse_datetime(event_data['end_time'])
            
            if start_time >= end_time:
                return {'success': False, 'error': "Start time must be before end time"}
            
            # Check for conflicts (only for non-recurring events)
            if event_data.get('recurrence') == 'none':
                calendar = self.load_user_calendar(user_id)
                if not calendar.check_availability(start_time, end_time):
                    return {'success': False, 'error': "Time slot conflicts with existing event"}
            
            # Prepare document for MongoDB
            doc = {
                'user_id': user_id,
                'title': event_data['title'],
                'start_time': start_time,
                'end_time': end_time,
                'event_type': event_data['event_type'],
                'location': event_data.get('location'),
                'description': event_data.get('description'),
                'color': event_data.get('color', '#3498db'),
                'recurrence': event_data.get('recurrence', 'none'),
                'recurrence_end_date': self._parse_datetime(event_data['recurrence_end_date'])
                                      if event_data.get('recurrence_end_date') else None,
                'reminders': event_data.get('reminders', [15, 60]),
                'created_at': datetime.now(timezone.utc)
            }
            
            result = self.collection.insert_one(doc)
            return {'success': True, 'event_id': str(result.inserted_id)}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_event(self, event_id: str, user_id: str) -> Optional[Dict]:
        """Get a single event (user-scoped for security)."""
        try:
            event = self.collection.find_one({
                '_id': ObjectId(event_id),
                'user_id': user_id
            })
            if event:
                event['_id'] = str(event['_id'])
            return event
        except Exception:
            return None
    
    def get_user_events(self, user_id: str, start: Optional[datetime] = None,
                       end: Optional[datetime] = None) -> List[Dict]:
        """Get all events for a user, optionally in a date range."""
        try:
            query = {'user_id': user_id}
            
            if start and end:
                query['start_time'] = {'$gte': start}
                query['end_time'] = {'$lte': end}
            
            events = list(self.collection.find(query).sort('start_time', 1))
            for event in events:
                event['_id'] = str(event['_id'])
            return events
        except Exception:
            return []
    
    def update_event(self, event_id: str, user_id: str, update_data: Dict) -> Dict:
        """
        Update an event (with conflict checking if times changed).
        
        Args:
            event_id: Event to update
            user_id: User who owns the event
            update_data: Fields to update
        
        Returns:
            {success: bool, error: str or None}
        """
        try:
            # Get current event to check what's changing
            current = self.get_event(event_id, user_id)
            if not current:
                return {'success': False, 'error': 'Event not found'}
            
            # Parse datetime fields
            if 'start_time' in update_data:
                update_data['start_time'] = self._parse_datetime(update_data['start_time'])
            if 'end_time' in update_data:
                update_data['end_time'] = self._parse_datetime(update_data['end_time'])
            if 'recurrence_end_date' in update_data and update_data['recurrence_end_date']:
                update_data['recurrence_end_date'] = self._parse_datetime(update_data['recurrence_end_date'])
            
            # Check for conflicts if times changed
            if 'start_time' in update_data or 'end_time' in update_data:
                new_start = update_data.get('start_time', self._parse_datetime(current['start_time']))
                new_end = update_data.get('end_time', self._parse_datetime(current['end_time']))
                
                calendar = self.load_user_calendar(user_id)
                if not calendar.check_availability(new_start, new_end):
                    return {'success': False, 'error': 'New time conflicts with existing event'}
            
            # Update in MongoDB
            result = self.collection.update_one(
                {'_id': ObjectId(event_id), 'user_id': user_id},
                {'$set': update_data}
            )
            
            return {'success': result.modified_count > 0}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_event(self, event_id: str, user_id: str, delete_future: bool = False, from_date: Optional[datetime] = None) -> Dict:
        """Delete an event."""
        try:
            # If deleting future occurrences of a recurring event, we truncate the recurrence
            if delete_future:
                # Ensure from_date is timezone-aware
                if from_date is None:
                    from_date = datetime.now(timezone.utc)
                else:
                    if from_date.tzinfo is None:
                        from_date = from_date.replace(tzinfo=timezone.utc)
                    else:
                        from_date = from_date.astimezone(timezone.utc)

                # Load event doc
                event = self.get_event(event_id, user_id)
                if not event:
                    return {'success': False, 'error': 'Event not found'}

                # If it's not a recurring event, deleting future == deleting the event
                if event.get('recurrence', 'none') == 'none':
                    result = self.collection.delete_one({'_id': ObjectId(event_id), 'user_id': user_id})
                    return {'success': result.deleted_count > 0}

                # Parse the original event start time
                try:
                    original_start = self._parse_datetime(event.get('start_time'))
                except Exception:
                    # Fallback: treat start_time as naive UTC
                    original_start = event.get('start_time')
                    if isinstance(original_start, datetime) and original_start.tzinfo is None:
                        original_start = original_start.replace(tzinfo=timezone.utc)

                # If from_date is at or before the original start: delete entire event
                if from_date <= original_start:
                    result = self.collection.delete_one({'_id': ObjectId(event_id), 'user_id': user_id})
                    return {'success': result.deleted_count > 0}

                # Otherwise, truncate the recurrence by setting recurrence_end_date to just before from_date
                new_end = from_date - timedelta(microseconds=1)
                update_result = self.collection.update_one(
                    {'_id': ObjectId(event_id), 'user_id': user_id},
                    {'$set': {'recurrence_end_date': new_end}}
                )
                # If modified_count is 0, maybe the date was already set earlier; return success True anyway
                return {'success': update_result.modified_count > 0 or update_result.matched_count > 0}

            # Default behavior: delete the event document entirely
            result = self.collection.delete_one({
                '_id': ObjectId(event_id),
                'user_id': user_id
            })
            return {'success': result.deleted_count > 0}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def load_user_calendar(self, user_id: str) -> Calendar:
        """
        Load user's calendar from database into in-memory Calendar object.
        
        This converts MongoDB docs into CalendarEvent objects and populates
        a Calendar object, ready for availability checking, free slot finding, etc.
        
        Args:
            user_id: User whose calendar to load
        
        Returns:
            Calendar object with all user's events
        """
        calendar = Calendar(user_id)
        events = self.get_user_events(user_id)
        
        for doc in events:
            try:
                event = CalendarEvent(
                    id=doc['_id'],
                    user_id=doc['user_id'],
                    title=doc['title'],
                    start_time=self._parse_datetime(doc['start_time']),
                    end_time=self._parse_datetime(doc['end_time']),
                    event_type=doc['event_type'],
                    location=doc.get('location'),
                    description=doc.get('description'),
                    color=doc.get('color', '#3498db'),
                    recurrence=doc.get('recurrence', 'none'),
                    recurrence_end_date=self._parse_datetime(doc['recurrence_end_date'])
                                       if doc.get('recurrence_end_date') else None,
                    reminders=doc.get('reminders', [15, 60])
                )
                calendar.add_event(event)
            except Exception as e:
                print(f"Error loading event {doc.get('_id')}: {e}")
                continue
        
        return calendar
    
    def find_free_slots(self, user_id: str, start: datetime, end: datetime,
                       min_duration: int = 30) -> Dict:
        """
        Find all free time slots for a user in a date range.
        
        Args:
            user_id: User to check
            start: Start of search range
            end: End of search range
            min_duration: Minimum free slot duration in minutes
        
        Returns:
            {success: bool, free_slots: [(start, end), ...], error: str or None}
        """
        try:
            calendar = self.load_user_calendar(user_id)
            slots = calendar.find_free_slots(start, end, min_duration)
            
            formatted = [
                {'start': slot[0].isoformat(), 'end': slot[1].isoformat()}
                for slot in slots
            ]
            
            return {'success': True, 'free_slots': formatted}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_statistics(self, user_id: str, start: datetime, end: datetime) -> Dict:
        """Get event statistics for a user in a date range."""
        try:
            calendar = self.load_user_calendar(user_id)
            stats = calendar.get_statistics(start, end)
            return {'success': True, 'statistics': stats}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ============================================================================
# In-memory fallback manager (for local development)
# ============================================================================
class InMemoryCalendarManager:
    """
    Lightweight in-memory calendar manager used when MongoDB is unavailable.
    Supports basic create/get/update/delete for development and testing.
    Data is not persisted.
    """
    def __init__(self):
        self._store = {}  # user_id -> list of event dicts

    def _ensure_user(self, user_id: str):
        if user_id not in self._store:
            self._store[user_id] = []

    def create_event(self, user_id: str, event_data: Dict) -> Dict:
        required = ['title', 'start_time', 'end_time', 'event_type']
        for field in required:
            if field not in event_data:
                return {'success': False, 'error': f"Missing field: {field}"}

        event_id = str(uuid.uuid4())
        ev = event_data.copy()
        ev['_id'] = event_id
        ev['user_id'] = user_id
        # store times as ISO strings for compatibility with API formatting
        self._ensure_user(user_id)
        self._store[user_id].append(ev)
        return {'success': True, 'event_id': event_id}

    def get_event(self, event_id: str, user_id: str) -> Optional[Dict]:
        self._ensure_user(user_id)
        for ev in self._store[user_id]:
            if ev.get('_id') == event_id:
                return ev.copy()
        return None

    def get_user_events(self, user_id: str, start: Optional[datetime] = None,
                        end: Optional[datetime] = None) -> List[Dict]:
        self._ensure_user(user_id)
        # No date filtering in fallback; return all events for now
        return [ev.copy() for ev in self._store[user_id]]

    def update_event(self, event_id: str, user_id: str, update_data: Dict) -> Dict:
        self._ensure_user(user_id)
        for ev in self._store[user_id]:
            if ev.get('_id') == event_id:
                ev.update(update_data)
                return {'success': True}
        return {'success': False, 'error': 'Event not found'}

    def delete_event(self, event_id: str, user_id: str, delete_future: bool = False, from_date: Optional[datetime] = None) -> Dict:
        self._ensure_user(user_id)
        for i, ev in enumerate(self._store[user_id]):
            if ev.get('_id') == event_id:
                del self._store[user_id][i]
                return {'success': True}
        return {'success': False, 'error': 'Event not found'}

    def find_free_slots(self, user_id: str, start: datetime, end: datetime, min_duration: int = 30) -> Dict:
        return {'success': False, 'error': 'Not implemented in in-memory fallback'}

    def get_statistics(self, user_id: str, start: datetime, end: datetime) -> Dict:
        return {'success': False, 'error': 'Not implemented in in-memory fallback'}

