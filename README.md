# Campus Compass

Campus Compass is a UF-focused web app for managing class schedules and campus events. It provides Google Sign‑in, calendar CRUD with recurrence support, free‑slot finding, event statistics, and UF building links.

## Key Features

- Google OAuth sign-in and user authentication
- Calendar event creation, update, deletion with recurrence support
- Free-slot finder to locate available time ranges
- Event statistics (total events, hours, averages, breakdowns)
- UF building code → campus map links (ICS processing helper)
- Guest/demo mode with sample read-only calendar

## Quick start (local development)

Requirements:

- Python 3.10+ (backend)
- Node 18+ / npm or yarn (frontend)
- MongoDB (optional for persistence)

Backend (FastAPI)

1. Install Python dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

2. Set environment variables (examples in `.env`):

- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` for Google OAuth
- MongoDB URI used by the backend (if available)

3. Run the backend:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (Vite + React + TypeScript)

1. Install frontend deps and run:

```bash
cd frontend
npm install
npm run dev
```

2. The frontend expects the backend at `http://localhost:8000` by default.

## Notes

- The README content is derived from the repository source (backend and frontend code), not external docs.
- Guest mode uses a built-in sample calendar; Google Sign‑in is required for real user actions.
- For production, configure secure OAuth credentials and a managed MongoDB instance.

## Contributing

Pull requests and issues welcome. For major changes, please open an issue first to discuss.

---
Happy coding! 🎓
