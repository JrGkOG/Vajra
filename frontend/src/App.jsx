import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Welcome } from './features/welcome/Welcome';
import { Login } from './features/auth/Login';
import { Home } from './features/home/Home';
import { UploadPage } from './features/upload/UploadPage';
import { VaultPage } from './features/vault/VaultPage';
import { FilesPage } from './features/files/FilesPage';
import { LogsPage } from './features/logs/LogsPage';
import { KeysPage } from './features/keys/KeysPage';
import { GenerateKeysPage } from './features/keys/GenerateKeysPage';
import { DocsPage } from './features/docs/DocsPage';
import { Navigation } from './components/Navigation';
import { Footer } from './components/Footer';

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

  // Protected route wrapper
  const ProtectedRoute = ({ children }) => {
    if (!user) {
      return <Navigate to="/login" replace />;
    }
    return (
      <>
        <Navigation user={user} onLogout={handleLogout} />
        <div className="flex flex-col min-h-screen">
          <div className="flex-1">
            {children}
          </div>
          <Footer />
        </div>
      </>
    );
  };

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Welcome />} />
        <Route
          path="/login"
          element={
            user ?
              <Navigate to="/home" replace /> :
              <Login onLogin={handleLogin} />
          }
        />

        {/* Public Documentation Route */}
        <Route path="/docs" element={<DocsPage />} />

        {/* Protected Routes */}
        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <Home token={token} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <UploadPage token={token} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vault"
          element={
            <ProtectedRoute>
              <VaultPage token={token} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/files"
          element={
            <ProtectedRoute>
              <FilesPage token={token} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/keys"
          element={
            <ProtectedRoute>
              <KeysPage token={token} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/generate-keys"
          element={
            <ProtectedRoute>
              <GenerateKeysPage token={token} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/logs"
          element={
            <ProtectedRoute>
              <LogsPage token={token} user={user} />
            </ProtectedRoute>
          }
        />

        {/* Legacy redirect for old dashboard route */}
        <Route path="/dashboard" element={<Navigate to="/home" replace />} />

        {/* Catch all - redirect to home or welcome */}
        <Route path="*" element={<Navigate to={user ? "/home" : "/"} replace />} />
      </Routes>
    </Router>
  );
}

export default App;
