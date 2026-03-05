# Google OAuth Setup Instructions

## Prerequisites
1. A Google Cloud Console account
2. Node.js and Python installed

## Step 1: Set up Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the Google+ API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized JavaScript origins:
     - `http://localhost:5173` (Vite dev server)
     - `http://localhost:3000` (if using different port)
   - Add authorized redirect URIs:
     - `http://localhost:5173`
     - `http://localhost:3000`
   - Click "Create"
   - Copy the Client ID (you'll need this!)

## Step 2: Configure Frontend

1. Copy the frontend environment template:
   ```powershell
   cp frontend\.env.example frontend\.env
   ```

2. Edit `frontend\.env` and add your Google Client ID:
   ```
   VITE_GOOGLE_CLIENT_ID=your-actual-client-id-here.apps.googleusercontent.com
   ```

## Step 3: Configure Backend

1. Copy the backend environment template:
   ```powershell
   cp backend\.env.example backend\.env
   ```

2. Edit `backend\.env` and add:
   - Your Google Client ID (same as frontend)
   - A secure SECRET_KEY for JWT tokens (generate a random string)

   ```
   GOOGLE_CLIENT_ID=your-actual-client-id-here.apps.googleusercontent.com
   SECRET_KEY=generate-a-secure-random-string-here
   ```

   To generate a secure secret key, you can use:
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

## Step 4: Install Backend Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

## Step 5: Run the Application

### Start Backend (Terminal 1):
```powershell
cd backend
python main.py
```
Backend will run on http://localhost:8000

### Start Frontend (Terminal 2):
```powershell
cd frontend
npm run dev
```
Frontend will run on http://localhost:5173

## Step 6: Test the Login

1. Open http://localhost:5173 in your browser
2. Click the "Sign in with Google" button
3. Sign in with your Google account
4. You'll be redirected back to the app with authentication

## Optional: Restrict to UFL Emails Only

If you want to only allow UFL email addresses, uncomment these lines in `backend/main.py`:

```python
# Optional: Restrict to UFL emails only
if not user_email.endswith("@ufl.edu"):
    raise HTTPException(status_code=403, detail="Only UFL email addresses are allowed")
```

## Security Notes

- Never commit `.env` files to git (they're in `.gitignore`)
- Use strong, random SECRET_KEY in production
- In production, update authorized origins and redirect URIs to your actual domain
- Store sensitive credentials in environment variables or secure vault services
