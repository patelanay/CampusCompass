import "../css/login.css";
import { useState } from "react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const validate = () => {
    if (!email || !password) {
      setError("Please enter both email and password.");
      return false;
    }
    // Basic email format check
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!re.test(email)) {
      setError("Please enter a valid email address.");
      return false;
    }
    setError(null);
    return true;
  };

  const onSubmit: React.FormEventHandler = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      // Placeholder: POST to backend login endpoint. Adapt URL as needed.
      const resp = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data?.message || "Login failed");
      }

      // On success: redirect or update app state. For now, simple reload.
      window.location.href = "/";
    } catch (err: unknown) {
      // Safely extract message from unknown error
      const message =
        err && typeof err === "object" && "message" in err
          ? String((err as { message?: unknown }).message)
          : "Login failed";
      setError(message);
    } finally {
      setLoading(false);
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

          <form className="auth-form" onSubmit={onSubmit}>
            <label className="label">
              Email
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@ufl.edu"
                required
              />
            </label>

            <label className="label">
              Password
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
              />
            </label>

            {error && <div className="error">{error}</div>}

            <button className="primary full" type="submit" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <div className="alt-note">
            Don't have an account? <button className="linkish">Sign Up</button>
          </div>
        </div>
      </div>
    </div>
  );
}
