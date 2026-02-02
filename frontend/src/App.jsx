import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Welcome } from './features/welcome/Welcome';
import { Login } from './features/auth/Login';
import { Dashboard } from './features/files/Dashboard';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  const handleLogin = (userData) => {
    setUser(userData.user);
    setToken(userData.token);
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
  };

  return (
    <Router>
      <Routes>
        {/* Home/Welcome Page */}
        <Route path="/" element={<Welcome />} />

        {/* Login Route */}
        <Route
          path="/login"
          element={
            user ?
              <Navigate to="/dashboard" replace /> :
              <Login onLogin={handleLogin} />
          }
        />

        {/* Dashboard Route - Protected */}
        <Route
          path="/dashboard"
          element={
            user ?
              <Dashboard user={user} token={token} onLogout={handleLogout} /> :
              <Navigate to="/login" replace />
          }
        />

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
