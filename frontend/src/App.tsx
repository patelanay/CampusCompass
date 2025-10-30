import Login from "./Login";
import Dashboard from "./Dashboard";
import "./css/app.css";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { useState, useEffect } from "react";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Check if user is logged in
    const user = localStorage.getItem("user");
    setIsLoggedIn(!!user);
  }, []);

  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ""}>
      <div className="app-inner">
        {isLoggedIn ? <Dashboard /> : <Login />}
      </div>
    </GoogleOAuthProvider>
  );
}

export default App;
