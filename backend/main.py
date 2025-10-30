import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests

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

app = FastAPI()

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

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

if __name__ == "__main__":
    uvicorn.run(app, host = "0.0.0.0", port = 8000)

#http://localhost:8000/docs
#http://localhost:8000/calendars