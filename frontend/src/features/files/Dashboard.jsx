import React from 'react';
import { Upload } from './Upload';
import { FileList } from './FileList';
import { LogOut, ShieldCheck } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Footer } from '../../components/Footer';

export const Dashboard = ({ user, token, onLogout }) => {
    return (
        <div className="min-h-screen bg-brutal-bg flex flex-col">
            <div className="flex-1 p-8">
                {/* Header */}
                <header className="flex justify-between items-center mb-12 border-b-4 border-black pb-4">
                    <div>
                        <h1 className="text-4xl font-black">COMMAND CENTER</h1>
                        <div className="flex items-center gap-2 mt-1">
                            <ShieldCheck size={20} />
                            <span className="font-mono bg-black text-white px-2">ROLE: {user.role.toUpperCase()}</span>
                        </div>
                    </div>
                    <Button onClick={onLogout} className="bg-white hover:bg-red-50">
                        <LogOut size={18} className="inline mr-2" /> DISCONNECT
                    </Button>
                </header>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Left Column: Upload */}
                    <div className="md:col-span-1">
                        <Upload token={token} />

                        <div className="mt-8 p-6 bg-yellow-100 border-4 border-black">
                            <h4 className="font-bold mb-2">SYSTEM STATUS</h4>
                            <ul className="list-disc list-inside font-mono text-sm space-y-1">
                                <li>ENCRYPTION: AES-256-GCM</li>
                                <li>STATUS: OPERATIONAL</li>
                                <li>LAST AUDIT: 12m ago</li>
                            </ul>
                        </div>
                    </div>

                    {/* Right Column: Files */}
                    <div className="md:col-span-2">
                        <FileList token={token} />
                    </div>
                </div>
            </div>

            {/* Footer */}
            <Footer />
        </div>
    );
};
