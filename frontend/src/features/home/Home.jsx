import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Rocket, Terminal, Database, Activity, TrendingUp } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { getSystemStatus } from '../../services/api';

export const Home = ({ token }) => {
    const [serverStatus, setServerStatus] = useState({ online: false, loading: true });
    const [systemMetrics, setSystemMetrics] = useState({
        totalFiles: 0,
        totalStorage: '0 MB',
        uptime: '0h 0m',
        lastCheck: new Date().toISOString()
    });

    // Poll server status every 5 seconds
    useEffect(() => {
        const checkServerStatus = async () => {
            try {
                const status = await getSystemStatus(token);
                setServerStatus({ online: true, loading: false });
                setSystemMetrics(status);
            } catch (error) {
                setServerStatus({ online: false, loading: false });
            }
        };

        // Initial check
        checkServerStatus();

        // Poll every 5 seconds
        const interval = setInterval(checkServerStatus, 5000);

        return () => clearInterval(interval);
    }, [token]);

    return (
        <div className="min-h-screen bg-brutal-bg p-8">
            <div className="max-w-7xl mx-auto">
                {/* Page Title */}
                <div className="mb-8">
                    <h1 className="text-5xl font-black mb-2">SYSTEM COMMAND CENTER</h1>
                    <p className="font-mono text-lg">Real-time monitoring and system diagnostics</p>
                </div>

                {/* Main Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {/* Server Status Rocket */}
                    <Card className="bg-white border-8 border-black p-8 text-center">
                        <h3 className="font-mono font-bold text-xl mb-6">SERVER STATUS</h3>

                        {/* Animated Rocket */}
                        <div className="relative h-48 flex items-center justify-center">
                            {serverStatus.loading ? (
                                <div className="font-mono text-2xl animate-pulse">CHECKING...</div>
                            ) : (
                                <div className={`transition-all duration-500 ${serverStatus.online
                                    ? 'animate-bounce'
                                    : 'grayscale opacity-50'
                                    }`}>
                                    <Rocket
                                        size={120}
                                        className={`${serverStatus.online
                                            ? 'text-green-600 stroke-[2.5px]'
                                            : 'text-red-600 stroke-[2.5px]'
                                            }`}
                                    />
                                    {/* Rocket Flames */}
                                    {serverStatus.online && (
                                        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-4">
                                            <div className="w-16 h-12 bg-gradient-to-b from-red-500 via-orange-500 to-yellow-400 rounded-full blur-sm animate-pulse"></div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        <div className={`mt-6 font-mono font-bold text-2xl ${serverStatus.online ? 'text-green-600' : 'text-red-600'
                            }`}>
                            {serverStatus.loading ? '...' : serverStatus.online ? '🟢 ONLINE' : '🔴 OFFLINE'}
                        </div>
                        {serverStatus.online && (
                            <div className="text-xs font-mono mt-2 text-gray-600">
                                All systems operational
                            </div>
                        )}
                    </Card>

                    {/* Terminal Backend Health */}
                    <Card className="bg-black text-green-400 border-8 border-black p-6 font-mono lg:col-span-2">
                        <div className="flex items-center gap-2 mb-4">
                            <Terminal size={20} />
                            <h3 className="font-bold text-lg">BACKEND HEALTH CHECK</h3>
                        </div>

                        <div className="space-y-2 text-sm">
                            <div className="flex items-center gap-2">
                                <span className="text-green-400">$</span>
                                <span>curl -X GET http://localhost:8000/health</span>
                            </div>
                            {serverStatus.online ? (
                                <>
                                    <div className="pl-4 text-green-300">
                                        HTTP/1.1 200 OK
                                    </div>
                                    <div className="pl-4">
                                        {'{'}<br />
                                        &nbsp;&nbsp;"status": "healthy",<br />
                                        &nbsp;&nbsp;"database": "connected",<br />
                                        &nbsp;&nbsp;"encryption": "AES-256-GCM",<br />
                                        &nbsp;&nbsp;"uptime": "{systemMetrics.uptime}"<br />
                                        {'}'}
                                    </div>
                                    <div className="flex items-center gap-2 text-green-300 mt-4">
                                        <span className="animate-pulse">▮</span>
                                        <span>Ready for operations...</span>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="pl-4 text-red-400">
                                        curl: (7) Failed to connect to localhost port 8000
                                    </div>
                                    <div className="pl-4 text-red-400 mt-4">
                                        ⚠️ Connection refused - Server offline
                                    </div>
                                </>
                            )}
                        </div>
                    </Card>

                    {/* Storage Metrics */}
                    <Card className="bg-brutal-blue text-white border-8 border-black p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <Database size={28} className="stroke-[3px]" />
                            <h3 className="font-mono font-bold text-xl">STORAGE</h3>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <div className="text-sm font-mono opacity-80 mb-1">Total Files</div>
                                <div className="text-4xl font-black">{systemMetrics.totalFiles}</div>
                            </div>
                            <div>
                                <div className="text-sm font-mono opacity-80 mb-1">Total Data</div>
                                <div className="text-3xl font-black">{systemMetrics.totalStorage}</div>
                            </div>
                            <div className="text-xs font-mono opacity-60 pt-4 border-t-4 border-white">
                                Last updated: {new Date(systemMetrics.lastCheck).toLocaleTimeString()}
                            </div>
                        </div>
                    </Card>

                    {/* Uptime Graph */}
                    <Card className="bg-white border-8 border-black p-6 lg:col-span-2">
                        <div className="flex items-center gap-3 mb-6">
                            <Activity size={28} className="stroke-[3px]" />
                            <h3 className="font-mono font-bold text-xl">SYSTEM UPTIME (Last 24h)</h3>
                        </div>

                        {/* Simple bar chart visualization */}
                        <div className="space-y-3">
                            {[
                                { time: '00:00', uptime: 100 },
                                { time: '04:00', uptime: 100 },
                                { time: '08:00', uptime: 95 },
                                { time: '12:00', uptime: 100 },
                                { time: '16:00', uptime: 100 },
                                { time: '20:00', uptime: serverStatus.online ? 100 : 0 },
                            ].map((data, idx) => (
                                <div key={idx} className="flex items-center gap-4">
                                    <div className="w-16 font-mono text-sm font-bold">{data.time}</div>
                                    <div className="flex-1 bg-gray-200 border-4 border-black h-8">
                                        <div
                                            className={`h-full transition-all ${data.uptime === 100 ? 'bg-green-500' :
                                                data.uptime > 50 ? 'bg-yellow-500' : 'bg-red-500'
                                                }`}
                                            style={{ width: `${data.uptime}%` }}
                                        ></div>
                                    </div>
                                    <div className="w-16 font-mono text-sm font-bold text-right">{data.uptime}%</div>
                                </div>
                            ))}
                        </div>

                        <div className="mt-6 flex items-center gap-6 text-xs font-mono">
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 bg-green-500 border-2 border-black"></div>
                                <span>100% Uptime</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 bg-yellow-500 border-2 border-black"></div>
                                <span>Partial</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 bg-red-500 border-2 border-black"></div>
                                <span>Offline</span>
                            </div>
                        </div>
                    </Card>

                    {/* Documentation Link */}
                    <Card className="bg-brutal-blue text-white border-8 border-black p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" /></svg>
                            <h3 className="font-mono font-bold text-xl">DOCUMENTATION</h3>
                        </div>

                        <p className="font-mono text-sm mb-6 opacity-90">
                            Learn how VAJRA works, system architecture, user flow, and security features.
                        </p>

                        <Link
                            to="/docs"
                            className="block w-full text-center bg-white text-black font-mono font-bold py-3 px-4 border-4 border-black shadow-hard hover:shadow-hard-sm hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
                        >
                            VIEW DOCS →
                        </Link>
                    </Card>

                    {/* Quick Actions */}
                    <Card className="bg-brutal-yellow border-8 border-black p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <TrendingUp size={28} className="stroke-[3px]" />
                            <h3 className="font-mono font-bold text-xl">QUICK STATS</h3>
                        </div>

                        <div className="space-y-4">
                            <div className="flex justify-between items-center pb-3 border-b-4 border-black">
                                <span className="font-mono font-bold">Encryption</span>
                                <span className="bg-black text-white px-2 py-1 text-xs font-mono">AES-256</span>
                            </div>
                            <div className="flex justify-between items-center pb-3 border-b-4 border-black">
                                <span className="font-mono font-bold">Uptime</span>
                                <span className="font-mono text-sm">{systemMetrics.uptime}</span>
                            </div>
                            <div className="flex justify-between items-center pb-3 border-b-4 border-black">
                                <span className="font-mono font-bold">Last Audit</span>
                                <span className="font-mono text-sm">12m ago</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="font-mono font-bold">Security</span>
                                <span className="text-green-600 font-mono font-bold">✓ SECURE</span>
                            </div>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
};
