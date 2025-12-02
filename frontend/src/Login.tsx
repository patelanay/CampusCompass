import "./css/login.css";
import { useState } from "react";
import { GoogleLogin, type CredentialResponse } from "@react-oauth/google";

export default function Login() {
  const [error, setError] = useState<string | null>(null);

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    try {
      // Send the Google token to your backend for verification
      const resp = await fetch("http://localhost:8000/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: credentialResponse.credential }),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data?.message || "Authentication failed");
      }

  const data = await resp.json();
  // Store user info returned by backend so App/Dashboard can read it
  // Expected shape: { user_email, user_name, user_id }
  localStorage.setItem("user", JSON.stringify(data));
  // ensure we are not leaving a stale guest flag set from a previous flow
  localStorage.removeItem("is_guest");
      
      // Redirect to the main app
      window.location.href = "/";
    } catch (err: unknown) {
      const message =
        err && typeof err === "object" && "message" in err
          ? String((err as { message?: unknown }).message)
          : "Authentication failed";
      setError(message);
    }
  };

  const handleGoogleError = () => {
    setError("Google Sign-In failed. Please try again.");
  };

  // Guest path: user clicked 'Continue as Guest' and we show a GoogleLogin specifically
  const [guestModePending, setGuestModePending] = useState(false);

  const handleGuestGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    try {
      // same backend verification flow
      const resp = await fetch("http://localhost:8000/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: credentialResponse.credential }),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data?.message || "Authentication failed");
      }

      const data = await resp.json();
      // store user info and mark session as a guest demo
      localStorage.setItem("user", JSON.stringify(data));
      localStorage.setItem("is_guest", "true");
      window.location.href = "/";
    } catch (err: unknown) {
      const message =
        err && typeof err === "object" && "message" in err
          ? String((err as { message?: unknown }).message)
          : "Authentication failed";
      setError(message);
    }
  };

  return (
    <div className="split-wrapper">
      <div className="panel left-panel">
        <div className="left-content">
          <h1 className="left-title">Campus Compass</h1>
          <p className="left-sub">UF's own Campus Companion!</p>
          <p className="left-copy">
            Campus Compass is your go-to app for navigating the University of
            Florida campus with ease. Whether you're a new student finding your
            way around or a returning student looking for the best spots, Campus
            Compass has got you covered.
          </p>
        </div>
        <div className="decor-circle decor-1"></div>
        <div className="decor-circle decor-2"></div>
      </div>

      <div className="panel right-panel">
        <div className="card">
          <h2 className="card-title">Sign in</h2>
          <p className="card-sub">
            Sign in using your UFL email to access your Campus Compass account
          </p>

          <form className="auth-form">
            {error && <div className="error">{error}</div>}
            
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              useOneTap
              text="signin_with"
              theme="filled_blue"
            />
          </form>

          {/* Guest mode requires signing in with Google, then the session will be marked read-only */}
          <div className="mt-4 text-center">
            {!guestModePending ? (
              <button
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                onClick={() => setGuestModePending(true)}
              >
                Continue as Guest (requires Google sign-in)
              </button>
            ) : (
              <div className="space-y-2 flex flex-col items-center">
                <div className="text-sm text-gray-600">Sign in with Google to continue as a guest demo (read-only).</div>
                <GoogleLogin
                  onSuccess={handleGuestGoogleSuccess}
                  onError={handleGoogleError}
                  text="signin_with"
                  theme="filled_blue"
                />
                <div>
                  <button
                    className="text-sm text-gray-500 underline mt-1"
                    onClick={() => setGuestModePending(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
            <div className="text-sm text-gray-500 mt-2">Guest mode will keep the app read-only for demo purposes.</div>
          </div>
          <div className="alt-note">
            Sign in with your Google account to access Campus Compass
          </div>
        </div>
      </div>
    </div>
  );
}
