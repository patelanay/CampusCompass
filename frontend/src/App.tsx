import { useEffect, useState } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";

import Dashboard from "./Dashboard";
import Login from "./Login";
import "./css/app.css";

function hasStoredUser(): boolean {
  try {
    return Boolean(localStorage.getItem("user"));
  } catch {
    return false;
  }
}

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoggedIn(hasStoredUser());
    setIsLoading(false);
  }, []);

  if (isLoading) {
    return <div className="workspace-loader">Loading application...</div>;
  }

  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ""}>
      <div className="app-inner">{isLoggedIn ? <Dashboard /> : <Login />}</div>
    </GoogleOAuthProvider>
  );
}
