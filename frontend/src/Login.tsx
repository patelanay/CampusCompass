import "./css/login.css";
import { useState } from "react";
import { GoogleLogin, type CredentialResponse } from "@react-oauth/google";

export default function Login() {
  const [error, setError] = useState<string | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userData, setUserData] = useState<{ user_email: string; user_name: string; user_id: string } | null>(null);

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
      setUserData(data);
      setIsLoggedIn(true);
      setError(null);
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

  const handleContinueAsGuest = () => {
    // User has authenticated, now set guest mode
    if (userData) {
      const guest = {
        user_email: userData.user_email,
        user_name: userData.user_name,
        user_id: "guest",
      };
      localStorage.setItem("user", JSON.stringify(guest));
      window.location.href = "/";
    }
  };

  const handleContinueAsNormalUser = () => {
    // User has authenticated, use their real credentials
    if (userData) {
      localStorage.setItem("user", JSON.stringify(userData));
      window.location.href = "/";
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

            {!isLoggedIn ? (
              <>
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  useOneTap
                  text="signin_with"
                  theme="filled_blue"
                />

                {/* Guest mode option - still shows same UI but requires login first */}
                <div className="mt-4 text-center">
                  <button
                    type="button"
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 cursor-not-allowed opacity-50"
                    disabled
                  >
                    Continue as Guest
                  </button>
                  <div className="text-sm text-gray-500 mt-2">
                    Sign in first to access guest mode
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="success-message mb-4 p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
                  ✓ Signed in as {userData?.user_name} ({userData?.user_email})
                </div>

                <div className="flex flex-col gap-3">
                  <button
                    type="button"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                    onClick={handleContinueAsNormalUser}
                  >
                    Continue as {userData?.user_name}
                  </button>

                  <button
                    type="button"
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition"
                    onClick={handleContinueAsGuest}
                  >
                    Continue as Guest
                  </button>
                </div>

                <div className="text-sm text-gray-500 mt-2">
                  Guest mode allows viewing a sample calendar (read-only).
                </div>
              </>
            )}
          </form>

          <div className="alt-note">
            Sign in with your Google account to access Campus Compass
          </div>
        </div>
      </div>
    </div>
  );
}
