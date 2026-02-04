import React from 'react';
import { Link } from 'react-router-dom';
import {
    BookOpen, Shield, Lock, Key, Upload, Download,
    Database, Server, Zap, FileText, CheckCircle, ArrowRight
} from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Footer } from '../../components/Footer';

export const DocsPage = () => {
    return (
        <div className="min-h-screen bg-brutal-bg p-8">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-4 mb-4">
                        <BookOpen size={48} className="stroke-[3px]" />
                        <h1 className="text-5xl font-black">DOCUMENTATION</h1>
                    </div>
                    <p className="font-mono text-lg">
                        Complete guide to VAJRA's secure file sharing system
                    </p>
                </div>

                {/* System Overview */}
                <Card className="bg-white border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-4 flex items-center gap-3">
                        <Shield size={32} />
                        SYSTEM OVERVIEW
                    </h2>
                    <p className="font-mono mb-4">
                        VAJRA is a Zero-Trust, Quantum-Resistant file sharing system designed for
                        satellite telemetry data exchange with military-grade security.
                    </p>
                    <div className="space-y-2 font-mono text-sm">
                        <div className="flex items-start gap-2">
                            <CheckCircle size={20} className="text-green-600 flex-shrink-0 mt-0.5" />
                            <span><strong>AES-256-GCM Encryption:</strong> All files encrypted at rest and in transit</span>
                        </div>
                        <div className="flex items-start gap-2">
                            <CheckCircle size={20} className="text-green-600 flex-shrink-0 mt-0.5" />
                            <span><strong>Chunked Storage:</strong> Files split into 1MB encrypted chunks</span>
                        </div>
                        <div className="flex items-start gap-2">
                            <CheckCircle size={20} className="text-green-600 flex-shrink-0 mt-0.5" />
                            <span><strong>Ed25519 Signatures:</strong> Cryptographic file integrity verification</span>
                        </div>
                        <div className="flex items-start gap-2">
                            <CheckCircle size={20} className="text-green-600 flex-shrink-0 mt-0.5" />
                            <span><strong>Role-Based Access:</strong> Admin, Operator, Engineer clearance levels</span>
                        </div>
                        <div className="flex items-start gap-2">
                            <CheckCircle size={20} className="text-green-600 flex-shrink-0 mt-0.5" />
                            <span><strong>Email-Based MFA:</strong> Two-factor authentication for all users</span>
                        </div>
                    </div>
                </Card>

                {/* Architecture & Security */}
                <Card className="bg-brutal-yellow border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-4 flex items-center gap-3 text-black">
                        <Server size={32} />
                        ARCHITECTURE & SECURITY
                    </h2>
                    <div className="space-y-4 font-mono text-black">
                        <div className="bg-white border-4 border-black p-4">
                            <h3 className="font-bold mb-2">Frontend (React)</h3>
                            <p className="text-sm mb-2">Modern web interface with security-first design</p>
                            <ul className="text-sm space-y-1 ml-4">
                                <li>🔐 <strong>Client-side encryption</strong> before upload</li>
                                <li>🔐 <strong>Secure headers</strong> for sensitive data transmission</li>
                                <li>🔐 <strong>No sensitive data in URLs</strong> (all via HTTP headers)</li>
                            </ul>
                        </div>
                        <div className="bg-white border-4 border-black p-4">
                            <h3 className="font-bold mb-2">Backend (FastAPI + Python)</h3>
                            <p className="text-sm mb-2">RESTful API with cryptographic security</p>
                            <ul className="text-sm space-y-1 ml-4">
                                <li>🔐 <strong>AES-256-GCM encryption</strong> for all file chunks</li>
                                <li>🔐 <strong>Ed25519 signatures</strong> for integrity verification</li>
                                <li>🔐 <strong>JWT tokens</strong> for authenticated requests</li>
                                <li>🔐 <strong>Role-based access control</strong> (RBAC)</li>
                            </ul>
                        </div>
                        <div className="bg-white border-4 border-black p-4">
                            <h3 className="font-bold mb-2">Authentication & Storage (Supabase)</h3>
                            <p className="text-sm mb-2">Enterprise-grade auth and data storage</p>
                            <ul className="text-sm space-y-1 ml-4">
                                <li>🔐 <strong>Email-based MFA</strong> (Multi-Factor Authentication)</li>
                                <li>🔐 <strong>Secure PostgreSQL database</strong> for metadata</li>
                                <li>🔐 <strong>Row-level security</strong> policies</li>
                                <li>🔐 <strong>Encrypted storage</strong> for all data at rest</li>
                            </ul>
                        </div>
                    </div>
                </Card>

                {/* User Flow */}
                <Card className="bg-brutal-blue text-white border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-6 flex items-center gap-3">
                        <ArrowRight size={32} />
                        USER FLOW
                    </h2>

                    <div className="space-y-6">
                        {/* Step 1 */}
                        <div className="bg-white text-black border-4 border-black p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="bg-brutal-yellow px-3 py-1 border-2 border-black font-black">1</div>
                                <h3 className="font-black text-xl">AUTHENTICATION</h3>
                            </div>
                            <p className="font-mono text-sm">
                                User enters email & password → Backend sends 6-digit MFA code to email →
                                User verifies code → Receives JWT token
                            </p>
                        </div>

                        {/* Step 2 */}
                        <div className="bg-white text-black border-4 border-black p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="bg-brutal-yellow px-3 py-1 border-2 border-black font-black">2</div>
                                <h3 className="font-black text-xl">KEY GENERATION</h3>
                            </div>
                            <p className="font-mono text-sm">
                                Navigate to "GEN KEYS" → Create vault password → Backend generates Ed25519
                                signature key pair → Private key encrypted with vault password →
                                Public key registered for future file signing
                            </p>
                        </div>

                        {/* Step 3 */}
                        <div className="bg-white text-black border-4 border-black p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="bg-brutal-yellow px-3 py-1 border-2 border-black font-black">3</div>
                                <h3 className="font-black text-xl">FILE UPLOAD</h3>
                            </div>
                            <p className="font-mono text-sm">
                                Select classification (Public/Mission Logs/Top Secret) →
                                Choose file → Optionally provide vault password for signing →
                                File split into 1MB chunks → Each chunk encrypted with AES-256-GCM →
                                Optional: File hash signed with private key → Chunks stored in database
                            </p>
                        </div>

                        {/* Step 4 */}
                        <div className="bg-white text-black border-4 border-black p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="bg-brutal-yellow px-3 py-1 border-2 border-black font-black">4</div>
                                <h3 className="font-black text-xl">FILE ACCESS</h3>
                            </div>
                            <p className="font-mono text-sm">
                                View files in "VAULT" → See paginated list (10 files/page) →
                                Check file details (name, classification, chunks, owner)
                            </p>
                        </div>

                        {/* Step 5 */}
                        <div className="bg-white text-black border-4 border-black p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="bg-brutal-yellow px-3 py-1 border-2 border-black font-black">5</div>
                                <h3 className="font-black text-xl">INTEGRITY CHECK</h3>
                            </div>
                            <p className="font-mono text-sm">
                                Click "CHECK" button → Backend verifies chunk integrity and signature →
                                Shows detailed results (chunk status, signature verification) →
                                Indicates if file is safe to download
                            </p>
                        </div>

                        {/* Step 6 */}
                        <div className="bg-white text-black border-4 border-black p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="bg-brutal-yellow px-3 py-1 border-2 border-black font-black">6</div>
                                <h3 className="font-black text-xl">FILE DOWNLOAD</h3>
                            </div>
                            <p className="font-mono text-sm mb-2">Two methods:</p>
                            <div className="ml-4 space-y-2 text-sm">
                                <div>
                                    <strong>KEY Method:</strong> Opens vault dialog → Select stored vault key →
                                    Backend decrypts private key → Reassembles & decrypts chunks → Downloads file
                                </div>
                                <div>
                                    <strong>DL (Manual) Method:</strong> Prompts for vault password →
                                    Same process with entered password
                                </div>
                            </div>
                        </div>
                    </div>
                </Card>

                {/* Security Technologies */}
                <Card className="bg-brutal-pink text-white border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-4 flex items-center gap-3">
                        <Zap size={32} />
                        SECURITY TECHNOLOGIES
                    </h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        <div className="bg-white text-black border-4 border-black p-4">
                            <h3 className="font-black mb-2">Encryption & Signing</h3>
                            <ul className="font-mono text-sm space-y-1">
                                <li>🔐 <strong>AES-256-GCM</strong> - File encryption</li>
                                <li>🔐 <strong>Ed25519</strong> - Digital signatures</li>
                                <li>🔐 <strong>SHA-256</strong> - Hash functions</li>
                                <li>🔐 <strong>PBKDF2</strong> - Key derivation</li>
                            </ul>
                        </div>
                        <div className="bg-white text-black border-4 border-black p-4">
                            <h3 className="font-black mb-2">Authentication & Access</h3>
                            <ul className="font-mono text-sm space-y-1">
                                <li>🔐 <strong>Email MFA</strong> - Two-factor auth</li>
                                <li>🔐 <strong>JWT</strong> - Secure session tokens</li>
                                <li>🔐 <strong>RBAC</strong> - Role-based access</li>
                                <li>🔐 <strong>Supabase Auth</strong> - Enterprise auth</li>
                            </ul>
                        </div>
                        <div className="bg-white text-black border-4 border-black p-4">
                            <h3 className="font-black mb-2">Data Protection</h3>
                            <ul className="font-mono text-sm space-y-1">
                                <li>🔐 <strong>Chunked storage</strong> - 1MB encrypted chunks</li>
                                <li>🔐 <strong>Zero-Trust design</strong> - Never trust, verify</li>
                                <li>🔐 <strong>Secure headers</strong> - No URL leaks</li>
                                <li>🔐 <strong>Row-level security</strong> - Database isolation</li>
                            </ul>
                        </div>
                        <div className="bg-white text-black border-4 border-black p-4">
                            <h3 className="font-black mb-2">Audit & Compliance</h3>
                            <ul className="font-mono text-sm space-y-1">
                                <li>🔐 <strong>Immutable logs</strong> - All actions tracked</li>
                                <li>🔐 <strong>Integrity checks</strong> - Tamper detection</li>
                                <li>🔐 <strong>Classification levels</strong> - Data separation</li>
                                <li>🔐 <strong>Forensic verification</strong> - Signature validation</li>
                            </ul>
                        </div>
                    </div>
                </Card>

                {/* Key Features */}
                <Card className="bg-white border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-4 flex items-center gap-3">
                        <Key size={32} />
                        KEY FEATURES
                    </h2>
                    <div className="space-y-4">
                        <div className="border-4 border-black p-4 bg-brutal-bg">
                            <h3 className="font-black mb-2 flex items-center gap-2">
                                <Lock size={20} />
                                Vault Key Management
                            </h3>
                            <p className="font-mono text-sm">
                                Store multiple vault keys with labels. Reuse keys for quick downloads
                                without re-entering passwords.
                            </p>
                        </div>
                        <div className="border-4 border-black p-4 bg-brutal-bg">
                            <h3 className="font-black mb-2 flex items-center gap-2">
                                <FileText size={20} />
                                File Pagination
                            </h3>
                            <p className="font-mono text-sm">
                                View 10 files per page with next/prev navigation. Shows file count
                                and current page range.
                            </p>
                        </div>
                        <div className="border-4 border-black p-4 bg-brutal-bg">
                            <h3 className="font-black mb-2 flex items-center gap-2">
                                <CheckCircle size={20} />
                                Integrity Verification
                            </h3>
                            <p className="font-mono text-sm">
                                Verify file integrity before download. Check chunk completeness and
                                signature validity. See detailed pass/fail status.
                            </p>
                        </div>
                        <div className="border-4 border-black p-4 bg-brutal-bg">
                            <h3 className="font-black mb-2 flex items-center gap-2">
                                <Database size={20} />
                                Real-time Storage Stats
                            </h3>
                            <p className="font-mono text-sm">
                                Home page displays actual file count and storage usage calculated from
                                chunk data (1MB per chunk).
                            </p>
                        </div>
                    </div>
                </Card>

                {/* Security Notice */}
                <Card className="bg-brutal-green border-8 border-black p-8">
                    <h2 className="text-3xl font-black mb-4 flex items-center gap-3 text-black">
                        <Shield size={32} />
                        SECURITY NOTICE
                    </h2>
                    <div className="space-y-3 font-mono text-sm text-black">
                        <p>
                            <strong>✓ SECURE:</strong> Vault passwords and public keys transmitted via
                            HTTP headers (X-Vault-Password, X-Public-Key), NOT URL query parameters
                        </p>
                        <p>
                            <strong>✓ ENCRYPTED:</strong> All files encrypted before storage.
                            Original files never stored in plaintext.
                        </p>
                        <p>
                            <strong>✓ VERIFIED:</strong> Ed25519 signatures ensure file authenticity
                            and detect tampering.
                        </p>
                        <p>
                            <strong>✓ ISOLATED:</strong> Each user's private key encrypted with
                            their unique vault password.
                        </p>
                    </div>
                </Card>

                {/* Back Button */}
                <div className="mt-8 text-center">
                    <Link
                        to="/"
                        className="inline-block font-mono font-bold px-8 py-4 border-4 border-black bg-brutal-yellow hover:bg-yellow-400 shadow-hard hover:shadow-hard-sm hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
                    >
                        ← BACK TO WELCOME
                    </Link>
                </div>
            </div>

            {/* Footer */}
            <Footer />
        </div>
    );
};
