import Login from "./Login";
import Dashboard from "./Dashboard";
import "./css/app.css";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { useState, useEffect } from "react";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    try {
      const user = localStorage.getItem("user");
      setIsLoggedIn(!!user);
    } catch (error) {
      console.error("Error checking login status:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ""}>
      <div className="app-inner">{isLoggedIn ? <Dashboard /> : <Login />}</div>
    </GoogleOAuthProvider>
  );
}

export default App;
