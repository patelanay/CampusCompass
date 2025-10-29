import { useEffect, useState } from "react";
import "./css/app.css";

interface UserData {
  user_name: string;
  user_email: string;
  user_id: string;
}

export default function Dashboard() {
  const [user, setUser] = useState<UserData | null>(null);

  useEffect(() => {
    // Get user data from localStorage
    const userData = localStorage.getItem("user");
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("user");
    window.location.href = "/";
  };

  if (!user) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
      <div style={{ 
        background: "white", 
        padding: "2rem", 
        borderRadius: "8px", 
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)" 
      }}>
        <h1 style={{ marginBottom: "1rem", color: "#003087" }}>
          Hello, {user.user_name}!
        </h1>
        <p style={{ fontSize: "1.1rem", color: "#666", marginBottom: "2rem" }}>
          Email: {user.user_email}
        </p>
        
        <button 
          onClick={handleLogout}
          style={{
            padding: "0.75rem 1.5rem",
            background: "#FA4616",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "1rem"
          }}
        >
          Logout
        </button>
      </div>

      <div style={{ marginTop: "2rem", padding: "1.5rem", background: "white", borderRadius: "8px" }}>
        <h2 style={{ color: "#003087", marginBottom: "1rem" }}>Welcome to Campus Compass!</h2>
        <p style={{ color: "#666" }}>
          Your campus navigation companion for the University of Florida.
        </p>
      </div>
    </div>
  );
}
