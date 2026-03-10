import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "@/pages/Login";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";
import Dashboard from "@/pages/Dashboard";
import Calendar from "@/pages/Calendar";
import Employees from "@/pages/Employees";
import Holidays from "@/pages/Holidays";
import { Toaster } from "@/components/ui/sonner";

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if user is logged in
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  return (
    <div className="App">
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              user ? <Navigate to="/dashboard" /> : <Login onLogin={handleLogin} />
            }
          />
          <Route
            path="/forgot-password"
            element={
              user ? <Navigate to="/dashboard" /> : <ForgotPassword />
            }
          />
          <Route
            path="/reset-password"
            element={
              user ? <Navigate to="/dashboard" /> : <ResetPassword />
            }
          />
          <Route
            path="/dashboard"
            element={
              user ? (
                <Dashboard user={user} onLogout={handleLogout} />
              ) : (
                <Navigate to="/" />
              )
            }
          />
          <Route
            path="/calendar"
            element={
              user ? (
                <Calendar user={user} onLogout={handleLogout} />
              ) : (
                <Navigate to="/" />
              )
            }
          />
          <Route
            path="/employees"
            element={
              user && user.role === "hr" ? (
                <Employees user={user} onLogout={handleLogout} />
              ) : (
                <Navigate to="/dashboard" />
              )
            }
          />
          <Route
            path="/holidays"
            element={
              user && user.role === "hr" ? (
                <Holidays user={user} onLogout={handleLogout} />
              ) : (
                <Navigate to="/dashboard" />
              )
            }
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
