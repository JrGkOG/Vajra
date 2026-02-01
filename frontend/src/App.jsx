import React, { useState } from 'react';
import { Welcome } from './features/welcome/Welcome';
import { Login } from './features/auth/Login';
import { Dashboard } from './features/files/Dashboard';

function App() {
  const [view, setView] = useState('welcome'); // 'welcome' | 'login' | 'dashboard'
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  const handleEnterSystem = () => {
    setView('login');
  };

  const handleLogin = (userData) => {
    setUser(userData.user);
    setToken(userData.token);
    setView('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    setView('welcome');
  };

  if (view === 'welcome') {
    return <Welcome onEnter={handleEnterSystem} />;
  }

  if (view === 'login') {
    return <Login onLogin={handleLogin} />;
  }

  return <Dashboard user={user} token={token} onLogout={handleLogout} />;
}

export default App;
