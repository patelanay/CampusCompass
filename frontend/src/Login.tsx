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

          <div className="alt-note">
            Sign in with your Google account to access Campus Compass
          </div>
        </div>
      </div>
    </div>
  );
}
