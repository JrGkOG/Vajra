import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Lock, Zap, Database, ArrowRight, BookOpen, Link2, AlertTriangle } from 'lucide-react';
import { Footer } from '../../components/Footer';

export const Welcome = () => {
    return (
        <div className="min-h-screen bg-brutal-bg flex flex-col p-6">
            {/* Main Content */}
            <div className="flex-1 flex items-center justify-center">
                <div className="max-w-6xl w-full">
                    {/* Hero Section */}
                    <div className="text-center mb-20">
                        <div className="inline-block mb-10 p-12 bg-brutal-yellow border-8 border-black shadow-hard-xl">
                            <h1 className="text-9xl font-black tracking-tighter">VAJRA</h1>
                        </div>
                        <p className="text-4xl font-mono font-black mb-4 uppercase">
                            Next-Gen Satellite Telemetry Exchange
                        </p>
                        <p className="text-xl font-bold max-w-4xl mx-auto leading-relaxed">
                            A Zero-Trust, cryptographically sharded storage engine designed for high-latency mission data transfer between Ground Stations and Orbital Assets.
                        </p>
                    </div>

                    {/* Features Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-20">
                        {/* Card 1 - Yellow */}
                        <div className="brutal-card bg-brutal-yellow">
                            <div className="flex items-start gap-4 mb-4">
                                <Shield size={40} className="stroke-[3px] flex-shrink-0" />
                                <div>
                                    <h3 className="text-2xl font-black mb-3">CRYPTOGRAPHIC SHARDING</h3>
                                    <p className="text-base leading-relaxed">
                                        Files are fragmented into 512KB isolated chunks. No single file ever exists in a readable state on the server.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Card 2 - Pink */}
                        <div className="brutal-card bg-brutal-pink text-white">
                            <div className="flex items-start gap-4 mb-4">
                                <Lock size={40} className="stroke-[3px] flex-shrink-0" />
                                <div>
                                    <h3 className="text-2xl font-black mb-3">AES-256-GCM ENCRYPTION</h3>
                                    <p className="text-base leading-relaxed">
                                        Military-grade encryption applied at the source with Galois Counter Mode for simultaneous confidentiality and integrity.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Card 3 - Blue */}
                        <div className="brutal-card bg-brutal-blue text-white">
                            <div className="flex items-start gap-4 mb-4">
                                <Zap size={40} className="stroke-[3px] flex-shrink-0" />
                                <div>
                                    <h3 className="text-2xl font-black mb-3">ZERO-TRUST ACCESS</h3>
                                    <p className="text-base leading-relaxed">
                                        NIST-Compliant Multi-Factor Authentication (AAL2) is enforced for all classified payload retrieval.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Card 4 - Green */}
                        <div className="brutal-card bg-brutal-green">
                            <div className="flex items-start gap-4 mb-4">
                                <Database size={40} className="stroke-[3px] flex-shrink-0" />
                                <div>
                                    <h3 className="text-2xl font-black mb-3">IMMUTABLE AUDIT LOGS</h3>
                                    <p className="text-base leading-relaxed">
                                        Every upload, download, and access attempt is cryptographically logged for forensic verification.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Card 5 - Purple */}
                        <div className="brutal-card bg-brutal-purple text-white">
                            <div className="flex items-start gap-4 mb-4">
                                <Link2 size={40} className="stroke-[3px] flex-shrink-0" />
                                <div>
                                    <h3 className="text-2xl font-black mb-3">BLOCKCHAIN ANCHORING</h3>
                                    <p className="text-base leading-relaxed">
                                        Each file's Merkle root is written to a Solidity smart contract. Tamper with the database and the chain proves it.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Card 6 - Orange */}
                        <div className="brutal-card bg-brutal-orange text-white">
                            <div className="flex items-start gap-4 mb-4">
                                <AlertTriangle size={40} className="stroke-[3px] flex-shrink-0" />
                                <div>
                                    <h3 className="text-2xl font-black mb-3">ORACLE TAMPER ALARMS</h3>
                                    <p className="text-base leading-relaxed">
                                        An independent oracle inspects real storage and raises a permanent on-chain alarm on any mismatch.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* CTA */}
                    <div className="text-center">
                        <Link
                            to="/login"
                            className="brutal-btn bg-brutal-orange text-white text-2xl flex items-center gap-4 mx-auto mb-6"
                        >
                            <span>ENTER SYSTEM</span>
                            <ArrowRight size={32} className="stroke-[3px]" />
                        </Link>

                        {/* Documentation Button */}
                        <Link
                            to="/docs"
                            className="inline-block font-mono font-bold text-sm px-8 py-4 border-4 border-black bg-brutal-blue text-white hover:bg-blue-700 shadow-hard hover:shadow-hard-sm hover:translate-x-0.5 hover:translate-y-0.5 transition-all mb-6"
                        >
                            <BookOpen size={20} className="inline mr-2" />
                            VIEW FULL DOCUMENTATION
                        </Link>

                        <p className="mt-4 text-lg font-mono font-bold">
                            🔒 CLEARANCE REQUIRED • AUTHORIZED PERSONNEL ONLY
                        </p>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <Footer />
        </div>
    );
};
