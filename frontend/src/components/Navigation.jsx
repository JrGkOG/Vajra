import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Upload, Lock, FileText, LogOut, ShieldCheck, ScrollText, Link2 } from 'lucide-react';

export const Navigation = ({ user, onLogout }) => {
    // Compact so all links + logout sit on one row at laptop widths. The active
    // tab keeps its position (only the fill changes) so every button shares one baseline.
    const navLinkClass = ({ isActive }) => `
        flex items-center gap-1.5 px-3 py-2 text-sm font-mono font-bold border-4 border-black
        transition-all whitespace-nowrap
        ${isActive
            ? 'bg-brutal-yellow shadow-hard-sm'
            : 'bg-white hover:bg-gray-50 shadow-hard-sm hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-none'
        }
    `;

    return (
        <nav className="bg-brutal-bg border-b-8 border-black px-4 py-3 sticky top-0 z-50">
            <div className="max-w-screen-2xl mx-auto flex items-center justify-between gap-4">
                {/* Logo/Brand */}
                <div className="flex items-center gap-2 shrink-0">
                    <div className="bg-black text-white px-3 py-1.5 border-4 border-black font-black text-lg leading-none">
                        VAJRA
                    </div>
                    {user && (
                        <div className="flex items-center gap-1.5 bg-white border-4 border-black px-2 py-1">
                            <ShieldCheck size={14} />
                            <span className="font-mono text-xs font-bold leading-none">{user.role.toUpperCase()}</span>
                        </div>
                    )}
                </div>

                {/* Navigation Links */}
                {user && (
                    <div className="flex items-center justify-end gap-x-2 gap-y-3 flex-wrap">
                        <NavLink to="/home" className={navLinkClass}>
                            <Home size={16} className="hidden xl:block" />
                            HOME
                        </NavLink>
                        <NavLink to="/upload" className={navLinkClass}>
                            <Upload size={16} className="hidden xl:block" />
                            UPLOAD
                        </NavLink>
                        <NavLink to="/vault" className={navLinkClass}>
                            <Lock size={16} className="hidden xl:block" />
                            VAULT
                        </NavLink>
                        <NavLink to="/keys" className={navLinkClass}>
                            🔑 MY KEYS
                        </NavLink>
                        <NavLink to="/generate-keys" className={navLinkClass}>
                            ⚡ GEN KEYS
                        </NavLink>
                        <NavLink to="/files" className={navLinkClass}>
                            <FileText size={16} className="hidden xl:block" />
                            FILES
                        </NavLink>

                        <NavLink to="/chain" className={navLinkClass}>
                            <Link2 size={16} className="hidden xl:block" />
                            CHAIN
                        </NavLink>

                        {/* Admin-only Logs Link */}
                        {(user.permissions?.can_view_all_logs || user.role === 'admin') && (
                            <NavLink to="/logs" className={navLinkClass}>
                                <ScrollText size={16} className="hidden xl:block" />
                                LOGS
                            </NavLink>
                        )}

                        {/* Logout Button */}
                        <button
                            onClick={onLogout}
                            className="flex items-center gap-1.5 px-3 py-2 text-sm font-mono font-bold border-4 border-black bg-brutal-pink text-white hover:bg-pink-600 shadow-hard-sm hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5 transition-all whitespace-nowrap"
                        >
                            <LogOut size={16} className="hidden xl:block" />
                            LOGOUT
                        </button>
                    </div>
                )}
            </div>
        </nav>
    );
};
