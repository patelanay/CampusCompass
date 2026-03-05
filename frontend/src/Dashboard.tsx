import { useEffect, useState } from "react";

import Calendar from "./Calendar";
import Taskbar from "./Taskbar";
import "./css/app.css";

interface UserData {
  user_name: string;
  user_email: string;
  user_id: string;
}

function readStoredUser(): UserData | null {
  try {
    const rawUser = localStorage.getItem("user");
    return rawUser ? (JSON.parse(rawUser) as UserData) : null;
  } catch {
    return null;
  }
}

export default function Dashboard() {
  const [user, setUser] = useState<UserData | null>(null);

  useEffect(() => {
    setUser(readStoredUser());
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("user");
    window.location.href = "/";
  };

  const handleOpenCampusMap = () => {
    window.open("https://campusmap.ufl.edu/", "_blank", "noopener,noreferrer");
  };

  if (!user) {
    return <div className="workspace-loader">Loading dashboard...</div>;
  }

  return (
    <div className="app-shell">
      <div className="app-backdrop app-backdrop--blue" />
      <div className="app-backdrop app-backdrop--orange" />

      <header className="app-header glass-card">
        <div className="app-brand">
          <h1>Campus Compass</h1>
          <p>
            {user.user_name} · {user.user_email}
          </p>
        </div>
        <div className="app-actions">
          <button className="app-action-btn app-action-btn--secondary" onClick={handleOpenCampusMap}>
            Campus Map
          </button>
          <button className="app-action-btn" onClick={handleLogout}>
            Log Out
          </button>
        </div>
      </header>

      <main className="workspace">
        <div className="workspace-calendar">
          <Calendar userId={user.user_id} />
        </div>
        <div className="workspace-taskbar">
          <Taskbar userId={user.user_id} />
        </div>
      </main>
    </div>
  );
}
