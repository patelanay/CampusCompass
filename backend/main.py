import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

class Calendar(BaseModel):
    name: str

class Calendars(BaseModel):
    calendars: List[Calendar]

app = FastAPI()

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