import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
<<<<<<< Updated upstream
from typing import List
=======
from typing import List, Optional
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests
from calendar_manager import CalendarManager
from db_helpers import createMongoClient, loadEnvVariables
from pymongo import MongoClient
import uuid
from typing import Dict, Any

# Load environment variables
load_dotenv()
>>>>>>> Stashed changes

class Calendar(BaseModel):
    name: str

class Calendars(BaseModel):
    calendars: List[Calendar]

app = FastAPI()

<<<<<<< Updated upstream
=======

# Lightweight in-memory fallback when MongoDB/CalendarManager is unavailable
class InMemoryCalendarManager:
    def __init__(self):
        # user_id -> list of event dicts
        self.store: Dict[str, List[Dict[str, Any]]] = {}

    def _to_dt(self, value):
        if isinstance(value, datetime):
            return value
        try:
            v = value.replace('Z', '+00:00') if isinstance(value, str) and 'Z' in value else value
            dt = datetime.fromisoformat(v)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    def create_event(self, user_id: str, event_dict: Dict[str, Any]):
        ev = event_dict.copy()
        ev_id = str(uuid.uuid4())
        ev['_id'] = ev_id
        # normalize datetimes
        ev['start_time'] = self._to_dt(ev.get('start_time'))
        ev['end_time'] = self._to_dt(ev.get('end_time'))
        if user_id not in self.store:
            self.store[user_id] = []
        self.store[user_id].append(ev)
        return {'success': True, 'event_id': ev_id}

    def get_user_events(self, user_id: str, start_dt=None, end_dt=None):
        events = self.store.get(user_id, [])
        out = []
        for ev in events:
            st = ev.get('start_time')
            en = ev.get('end_time')
            if start_dt and st and st < start_dt:
                continue
            if end_dt and en and en > end_dt:
                continue
            out.append(ev)
        return out

    def get_event(self, event_id: str, user_id: str):
        for ev in self.store.get(user_id, []):
            if str(ev.get('_id')) == str(event_id):
                return ev
        return None

    def update_event(self, event_id: str, user_id: str, update_dict: Dict[str, Any]):
        ev = self.get_event(event_id, user_id)
        if not ev:
            return {'success': False, 'error': 'Event not found'}
        for k, v in update_dict.items():
            if k in ('start_time', 'end_time'):
                ev[k] = self._to_dt(v)
            else:
                ev[k] = v
        return {'success': True}

    def delete_event(self, event_id: str, user_id: str, delete_future: bool = False, from_date=None):
        events = self.store.get(user_id, [])
        for i, ev in enumerate(events):
            if str(ev.get('_id')) == str(event_id):
                del events[i]
                return {'success': True}
        return {'success': False}

    def find_free_slots(self, user_id: str, start_dt, end_dt, min_duration: int):
        # naive implementation: return full range as one free slot
        return {'success': True, 'free_slots': [{'start': start_dt.isoformat(), 'end': end_dt.isoformat()}]}

    def get_statistics(self, user_id: str, start_dt, end_dt):
        return {'success': True, 'count': len(self.store.get(user_id, []))}

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# Initialize MongoDB and CalendarManager
mongo_client: Optional[MongoClient] = None
calendar_manager: Optional[CalendarManager] = None

@app.on_event("startup")
async def startup_event():
    global mongo_client, calendar_manager
    try:
        uri = loadEnvVariables()
        mongo_client = createMongoClient(uri)
        calendar_manager = CalendarManager(mongo_client)
        print("CalendarManager initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize MongoDB/CalendarManager: {e}")
        print("Falling back to in-memory calendar manager (non-persistent). Calendar features will work for this session.")
        # Use in-memory fallback so the calendar endpoints still work without MongoDB
        try:
            calendar_manager = InMemoryCalendarManager()
            print("InMemoryCalendarManager initialized successfully")
        except Exception as e2:
            print(f"Failed to initialize InMemoryCalendarManager: {e2}")

@app.on_event("shutdown")
async def shutdown_event():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("MongoDB connection closed")

>>>>>>> Stashed changes
origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

memory_db = {"calendars":[]}

@app.get("/calendars", response_model=Calendars)
def get_calendars():
    # return the in-memory calendars list in the response model shape
    return {"calendars": memory_db["calendars"]}

@app.post("/calendars", response_model=Calendar)
def add_calendar(calendar: Calendar):
    memory_db["calendars"].append(calendar)
    return calendar

if __name__ == "__main__":
    uvicorn.run(app, host = "0.0.0.0", port = 8000)

#http://localhost:8000/docs
#http://localhost:8000/calendars