import React from 'react';
import { Shield, Lock, Zap, Database } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export const Welcome = ({ onEnter }) => {
    return (
        <div className="min-h-screen bg-brutal-bg flex items-center justify-center p-4">
            <div className="max-w-4xl w-full">
                {/* Hero Section */}
                <div className="text-center mb-12">
                    <div className="inline-block mb-6 p-4 bg-black">
                        <h1 className="text-7xl font-black text-brutal-yellow">VAJRA</h1>
                    </div>
                    <p className="text-2xl font-mono font-bold mb-4">SECURE FILE TRANSFER SYSTEM</p>
                    <p className="text-lg">Military-Grade Encryption • Zero-Trust Architecture</p>
                </div>

                {/* Features Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
                    <div className="brutal-card">
                        <div className="flex items-center gap-4 mb-3">
                            <Shield size={32} className="stroke-[3px]" />
                            <h3 className="text-xl font-bold">AES-256 ENCRYPTION</h3>
                        </div>
                        <p className="text-sm">Every file encrypted with military-grade AES-256-GCM before upload.</p>
                    </div>

                    <div className="brutal-card">
                        <div className="flex items-center gap-4 mb-3">
                            <Lock size={32} className="stroke-[3px]" />
                            <h3 className="text-xl font-bold">MFA REQUIRED</h3>
                        </div>
                        <p className="text-sm">Multi-factor authentication enforced for all file access.</p>
                    </div>

                    <div className="brutal-card">
                        <div className="flex items-center gap-4 mb-3">
                            <Zap size={32} className="stroke-[3px]" />
                            <h3 className="text-xl font-bold">ABAC POLICIES</h3>
                        </div>
                        <p className="text-sm">Attribute-based access control with role, status, and time checks.</p>
                    </div>

                    <div className="brutal-card">
                        <div className="flex items-center gap-4 mb-3">
                            <Database size={32} className="stroke-[3px]" />
                            <h3 className="text-xl font-bold">AUDIT LOGGING</h3>
                        </div>
                        <p className="text-sm">Immutable logs tracking every upload, download, and access denial.</p>
                    </div>
                </div>

                {/* CTA */}
                <div className="text-center">
                    <Button
                        onClick={onEnter}
                        className="text-xl px-12 py-4 bg-brutal-pink text-white hover:bg-pink-600"
                    >
                        ENTER SYSTEM →
                    </Button>
                    <p className="mt-4 text-xs font-mono">CLEARANCE REQUIRED • AUTHORIZED PERSONNEL ONLY</p>
                </div>
            </div>
        </div>
    );
};
