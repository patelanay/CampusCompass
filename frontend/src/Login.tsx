import { useState } from "react";
import { GoogleLogin, type CredentialResponse } from "@react-oauth/google";

import "./css/login.css";

interface AuthenticatedUser {
  user_email: string;
  user_name: string;
  user_id: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const AUTH_ENDPOINT = `${API_BASE_URL}/api/auth/google`;

export default function Login() {
  const [error, setError] = useState<string | null>(null);
  const [authenticatedUser, setAuthenticatedUser] = useState<AuthenticatedUser | null>(null);

  const saveUserAndReload = (user: AuthenticatedUser) => {
    localStorage.setItem("user", JSON.stringify(user));
    window.location.href = "/";
  };

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    try {
      if (!credentialResponse.credential) {
        throw new Error("Google credential was not returned.");
      }

      const response = await fetch(AUTH_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: credentialResponse.credential }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data?.detail || "Authentication failed");
      }

      const user = (await response.json()) as AuthenticatedUser;
      setAuthenticatedUser(user);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    }
  };

  const handleGoogleError = () => {
    setError("Google Sign-In failed. Please try again.");
  };

  return (
    <div className="login-page">
      <div className="login-bg login-bg--blue" />
      <div className="login-bg login-bg--orange" />

      <section className="login-shell">
        <div className="login-story glass-card">
          <p className="login-kicker">University of Florida</p>
          <h1>Campus Compass</h1>
          <p>
            Plan classes, keep track of assignments, and navigate UF with a cleaner daily workflow.
          </p>
          <ul>
            <li>Smart calendar with recurring events</li>
            <li>Task tracking with priorities</li>
            <li>Instant campus map access by building code</li>
          </ul>
        </div>

        <div className="login-card glass-card">
          <h2>Sign In</h2>
          <p>Use your UFL Google account to access Campus Compass.</p>

          {error && <div className="login-error">{error}</div>}

          {!authenticatedUser ? (
            <div className="login-actions">
              <GoogleLogin onSuccess={handleGoogleSuccess} onError={handleGoogleError} useOneTap text="signin_with" />
              <button type="button" className="login-btn login-btn--muted" disabled>
                Continue as Guest
              </button>
              <small>Sign in first to unlock guest demo mode.</small>
            </div>
          ) : (
            <div className="login-actions">
              <div className="login-success">
                Signed in as {authenticatedUser.user_name} ({authenticatedUser.user_email})
              </div>
              <button type="button" className="login-btn login-btn--primary" onClick={() => saveUserAndReload(authenticatedUser)}>
                Continue as {authenticatedUser.user_name}
              </button>
              <button
                type="button"
                className="login-btn login-btn--muted"
                onClick={() =>
                  saveUserAndReload({
                    user_email: authenticatedUser.user_email,
                    user_name: authenticatedUser.user_name,
                    user_id: "guest",
                  })
                }
              >
                Continue as Guest
              </button>
              <small>Guest mode is read-only and uses sample schedule data.</small>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
