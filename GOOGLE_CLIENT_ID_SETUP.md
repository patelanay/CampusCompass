# Quick Fix: Google OAuth Error 400

## The Problem
You're seeing "Error 400: invalid_request" because the Google Client ID is not configured.

## Solution: Get Your Google Client ID

### Step 1: Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Sign in with your Google account
3. Create a new project (or select an existing one)

### Step 2: Enable Google+ API
1. Go to **APIs & Services** > **Library**
2. Search for "Google+ API" (or "Google Identity Services API")
3. Click **Enable**

### Step 3: Create OAuth 2.0 Credentials
1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen first:
   - Choose **External** (unless you have a Google Workspace)
   - Fill in the required fields (App name, User support email, Developer contact)
   - Click **Save and Continue** through the steps
4. Back in Credentials, create OAuth client ID:
   - Application type: **Web application**
   - Name: "Campus Compass" (or any name)
   - **Authorized JavaScript origins:**
     - `http://localhost:5173`
     - `http://localhost:3000` (optional)
   - **Authorized redirect URIs:**
     - `http://localhost:5173`
     - `http://localhost:3000` (optional)
   - Click **Create**
5. **Copy the Client ID** (it looks like: `123456789-abcdefg.apps.googleusercontent.com`)

### Step 4: Add Client ID to Your .env File
1. Open `frontend/.env`
2. Add your Client ID:
   ```
   VITE_GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   ```
   Replace `your-client-id-here.apps.googleusercontent.com` with the actual Client ID you copied.

### Step 5: Restart the Frontend Server
1. Stop the frontend server (Ctrl+C)
2. Restart it:
   ```bash
   cd frontend
   npm run dev
   ```
3. Refresh your browser at http://localhost:5173

## Important Notes
- The `.env` file is in `.gitignore` - it won't be committed to git
- Make sure there are NO spaces around the `=` sign
- Don't include quotes around the Client ID
- The frontend dev server must be restarted after changing `.env` files

## Still Having Issues?
- Make sure `http://localhost:5173` is in your Authorized JavaScript origins
- Check that the OAuth consent screen is published (for testing, you can add test users)
- Verify the Client ID is correct (no extra spaces or characters)

