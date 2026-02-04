import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Upload, Lock, FileText, LogOut, ShieldCheck, ScrollText } from 'lucide-react';

export const Navigation = ({ user, onLogout }) => {
    const navLinkClass = ({ isActive }) => `
        flex items-center gap-2 px-4 py-3 font-mono font-bold border-4 border-black
        transition-all whitespace-nowrap
        ${isActive
            ? 'bg-brutal-yellow shadow-hard-sm translate-x-1 translate-y-1'
            : 'bg-white hover:bg-gray-50 shadow-hard hover:shadow-hard-sm hover:translate-x-0.5 hover:translate-y-0.5'
        }
    `;

    return (
        <nav className="bg-brutal-bg border-b-8 border-black p-4 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
                {/* Logo/Brand */}
                <div className="flex items-center gap-3">
                    <div className="bg-black text-white px-4 py-2 border-4 border-black font-black text-xl">
                        VAJRA
                    </div>
                    {user && (
                        <div className="flex items-center gap-2 bg-white border-4 border-black px-3 py-1">
                            <ShieldCheck size={16} />
                            <span className="font-mono text-sm font-bold">{user.role.toUpperCase()}</span>
                        </div>
                    )}
                </div>

                {/* Navigation Links */}
                {user && (
                    <div className="flex items-center gap-2 flex-wrap">
                        <NavLink to="/home" className={navLinkClass}>
                            <Home size={18} />
                            HOME
                        </NavLink>
                        <NavLink to="/upload" className={navLinkClass}>
                            <Upload size={18} />
                            UPLOAD
                        </NavLink>
                        <NavLink to="/vault" className={navLinkClass}>
                            <Lock size={18} />
                            VAULT
                        </NavLink>
                        <NavLink to="/keys" className={navLinkClass}>
                            🔑 MY KEYS
                        </NavLink>
                        <NavLink to="/generate-keys" className={navLinkClass}>
                            ⚡ GEN KEYS
                        </NavLink>
                        <NavLink to="/files" className={navLinkClass}>
                            <FileText size={18} />
                            FILES
                        </NavLink>

                        {/* Admin-only Logs Link */}
                        {(user.permissions?.can_view_all_logs || user.role === 'admin') && (
                            <NavLink to="/logs" className={navLinkClass}>
                                <ScrollText size={18} />
                                LOGS
                            </NavLink>
                        )}

                        {/* Logout Button */}
                        <button
                            onClick={onLogout}
                            className="flex items-center gap-2 px-4 py-3 font-mono font-bold border-4 border-black bg-brutal-pink text-white hover:bg-pink-600 shadow-hard hover:shadow-hard-sm hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
                        >
                            <LogOut size={18} />
                            LOGOUT
                        </button>
                    </div>
                )}
            </div>
        </nav>
    );
};
