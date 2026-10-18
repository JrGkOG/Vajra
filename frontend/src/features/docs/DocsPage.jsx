import React from 'react';
import { Link } from 'react-router-dom';
import {
    BookOpen, Shield, Lock, Key, Upload, Download,
    Database, Server, Zap, FileText, CheckCircle, ArrowRight,
    Link2, Anchor, Hash, Eye, AlertTriangle
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
                        <div className="flex items-start gap-2">
                            <CheckCircle size={20} className="text-green-600 flex-shrink-0 mt-0.5" />
                            <span><strong>Blockchain Anchoring:</strong> A Merkle root of every file's chunk hashes is written to a Solidity smart contract, so database tampering is detectable</span>
                        </div>
                        <div className="flex items-start gap-2">
                            <CheckCircle size={20} className="text-green-600 flex-shrink-0 mt-0.5" />
                            <span><strong>Hash-Chained Audit Ledger:</strong> Every log entry commits to the previous one; the head is pinned on-chain</span>
                        </div>
                        <div className="flex items-start gap-2">
                            <CheckCircle size={20} className="text-green-600 flex-shrink-0 mt-0.5" />
                            <span><strong>Oracle Monitoring:</strong> An independent wallet inspects real storage and raises an on-chain TamperAlarm</span>
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
                        <div className="bg-white border-4 border-black p-4">
                            <h3 className="font-bold mb-2">Blockchain Layer (Solidity + Hardhat + web3.py)</h3>
                            <p className="text-sm mb-2">Tamper-evidence the database owner cannot edit</p>
                            <ul className="text-sm space-y-1 ml-4">
                                <li>⛓️ <strong>VajraRegistry.sol</strong> - smart contract on an EVM chain</li>
                                <li>⛓️ <strong>Backend bridge</strong> - anchors roots, reads verdicts via web3.py</li>
                                <li>⛓️ <strong>Oracle node</strong> - separate wallet reporting what storage really holds</li>
                                <li>⛓️ <strong>Auto-start</strong> - backend launches the node, deploys, and replays its journal</li>
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
                                Optional: File hash signed with private key → Chunks stored in database →
                                Merkle root of all chunk hashes anchored on the blockchain
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
                                Click "CHECK" button → Backend compares the database against the on-chain
                                Merkle root, then verifies chunk integrity and signature →
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

                        {/* Step 7 */}
                        <div className="bg-white text-black border-4 border-black p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="bg-brutal-yellow px-3 py-1 border-2 border-black font-black">7</div>
                                <h3 className="font-black text-xl">BLOCKCHAIN VERIFICATION</h3>
                            </div>
                            <p className="font-mono text-sm">
                                Open "CHAIN" → See network status, contract address, latest block and anchored
                                file count → In "CHECK", the BLOCKCHAIN ANCHOR block shows the block number,
                                transaction hash and whether the on-chain root equals the database root
                            </p>
                        </div>

                        {/* Step 8 */}
                        <div className="bg-white text-black border-4 border-black p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="bg-brutal-yellow px-3 py-1 border-2 border-black font-black">8</div>
                                <h3 className="font-black text-xl">ORACLE TAMPER ALARM</h3>
                            </div>
                            <p className="font-mono text-sm">
                                Every 60 seconds (or on "RUN ORACLE CHECK") the contract requests a check →
                                Oracle reads the real stored chunks and recomputes the root → Reports it from a
                                separate wallet → Contract compares with the anchor → Mismatch raises a
                                permanent TamperAlarm event
                            </p>
                        </div>

                        {/* Step 9 */}
                        <div className="bg-white text-black border-4 border-black p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="bg-brutal-yellow px-3 py-1 border-2 border-black font-black">9</div>
                                <h3 className="font-black text-xl">AUDIT LEDGER (ADMIN)</h3>
                            </div>
                            <p className="font-mono text-sm">
                                "CHAIN" → "VERIFY LEDGER" walks the hash chain and names the first broken entry →
                                "ANCHOR HEAD ON-CHAIN" pins the latest hash in the contract so even a full
                                rewrite of the log is detected
                            </p>
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
                        <div className="bg-white text-black border-4 border-black p-4">
                            <h3 className="font-black mb-2">Blockchain Layer</h3>
                            <ul className="font-mono text-sm space-y-1">
                                <li>⛓️ <strong>Solidity contract</strong> - On-chain commitments</li>
                                <li>⛓️ <strong>Merkle tree</strong> - One root per file</li>
                                <li>⛓️ <strong>Hash chain</strong> - Tamper-evident audit log</li>
                                <li>⛓️ <strong>web3.py</strong> - Backend ↔ chain bridge</li>
                            </ul>
                        </div>
                        <div className="bg-white text-black border-4 border-black p-4">
                            <h3 className="font-black mb-2">Oracle & Monitoring</h3>
                            <ul className="font-mono text-sm space-y-1">
                                <li>🔮 <strong>Request / callback</strong> - Off-chain to on-chain</li>
                                <li>🔮 <strong>Separate wallet</strong> - Reports, never decides</li>
                                <li>🔮 <strong>TamperAlarm</strong> - Permanent on-chain event</li>
                                <li>🔮 <strong>Fail-silent</strong> - No false alarms if data unreachable</li>
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
                        <div className="border-4 border-black p-4 bg-brutal-bg">
                            <h3 className="font-black mb-2 flex items-center gap-2">
                                <Anchor size={20} />
                                On-Chain Anchoring
                            </h3>
                            <p className="font-mono text-sm">
                                Each upload writes the file's Merkle root and manifest hash to the smart
                                contract. Anchors are write-once and can be revoked but never erased.
                            </p>
                        </div>
                        <div className="border-4 border-black p-4 bg-brutal-bg">
                            <h3 className="font-black mb-2 flex items-center gap-2">
                                <AlertTriangle size={20} />
                                Automatic Tamper Alarms
                            </h3>
                            <p className="font-mono text-sm">
                                The oracle re-checks every anchored file on a schedule. A mismatch raises
                                a TamperAlarm event and the contract itself marks the file Compromised.
                            </p>
                        </div>
                        <div className="border-4 border-black p-4 bg-brutal-bg">
                            <h3 className="font-black mb-2 flex items-center gap-2">
                                <Hash size={20} />
                                Hash-Chained Audit Ledger
                            </h3>
                            <p className="font-mono text-sm">
                                Login, upload, download and log-view events are sealed into a hash chain.
                                Editing or deleting any entry breaks every hash after it.
                            </p>
                        </div>
                        <div className="border-4 border-black p-4 bg-brutal-bg">
                            <h3 className="font-black mb-2 flex items-center gap-2">
                                <Link2 size={20} />
                                Self-Starting, Self-Healing Chain
                            </h3>
                            <p className="font-mono text-sm">
                                Starting the backend launches the local node, deploys the contract (or
                                redeploys a stale one) and replays a hash-chained journal of earlier anchors.
                            </p>
                        </div>
                    </div>
                </Card>

                {/* Blockchain Concepts */}
                <Card className="bg-brutal-purple text-white border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-2 flex items-center gap-3">
                        <Link2 size={32} />
                        BLOCKCHAIN
                    </h2>
                    <p className="font-mono text-sm mb-4">Each concept below is implemented in this project, not just described.</p>
                    <div className="grid md:grid-cols-2 gap-4">
                        {[
                            ['Cryptographic hashing', 'SHA-256 fingerprints; changing one bit changes the whole hash.'],
                            ['Merkle tree & proof', 'Chunk hashes combine pairwise into one root; any single chunk can be proven with a few hashes.'],
                            ['Commitment scheme', 'Only the hash goes on-chain, so integrity is provable without revealing data.'],
                            ['Smart contract', 'VajraRegistry.sol enforces its own rules: roles, write-once anchors, monotonic checkpoints.'],
                            ['Immutability', 'Recorded commitments cannot be rewritten; revocation flags instead of deleting.'],
                            ['Hash chain', 'Each audit entry includes the previous hash, so history cannot be edited unnoticed.'],
                            ['Events', 'Cheap, permanent, searchable logs such as FileAnchored and TamperAlarm.'],
                            ['Access control', 'Owner, anchorer and oracle roles enforced by contract modifiers.'],
                            ['Oracle', 'Brings off-chain facts on-chain through a permissioned request/callback.'],
                            ['Transactions & gas', 'Every write is a mined transaction; roots are anchored instead of every event to save gas.'],
                            ['State replay', 'Chain state is rebuilt from history after a restart, as real nodes do.'],
                            ['Privacy by hashing', 'File ids are hashed before reaching the chain; no names, classes or identities.'],
                        ].map(([title, text]) => (
                            <div key={title} className="bg-white text-black border-4 border-black p-4">
                                <h3 className="font-black mb-1">{title}</h3>
                                <p className="font-mono text-sm">{text}</p>
                            </div>
                        ))}
                    </div>
                </Card>

                {/* On-chain vs off-chain */}
                <Card className="bg-white border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-4 flex items-center gap-3">
                        <Eye size={32} />
                        WHAT IS ON-CHAIN, AND WHAT IS NOT
                    </h2>
                    <div className="grid md:grid-cols-2 gap-4 font-mono text-sm">
                        <div className="border-4 border-black bg-green-50 p-4">
                            <div className="font-bold mb-2">ON-CHAIN (public, permanent)</div>
                            <ul className="list-disc ml-5 space-y-1">
                                <li>Merkle root of each file's encrypted chunk hashes</li>
                                <li>Hash of the signed file manifest</li>
                                <li>SHA-256 of the file id (never the id itself)</li>
                                <li>Audit-ledger head checkpoints</li>
                                <li>Oracle requests, reports and alarms</li>
                            </ul>
                        </div>
                        <div className="border-4 border-black bg-red-50 p-4">
                            <div className="font-bold mb-2">NEVER ON-CHAIN</div>
                            <ul className="list-disc ml-5 space-y-1">
                                <li>File contents or encryption keys</li>
                                <li>Filenames and classification levels</li>
                                <li>User identities or emails</li>
                                <li>Private signing keys</li>
                            </ul>
                        </div>
                    </div>
                </Card>

                {/* Oracle */}
                <Card className="bg-brutal-orange text-white border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-2 flex items-center gap-3">
                        <AlertTriangle size={32} />
                        HOW THE ORACLE WORKS
                    </h2>
                    <p className="font-mono text-sm mb-4">
                        A contract cannot read a database or a disk. The oracle is the trusted messenger that
                        carries what it saw back on-chain.
                    </p>
                    <div className="space-y-3">
                        {[
                            ['1', 'REQUEST', 'The contract emits IntegrityCheckRequested(requestId, fileId).'],
                            ['2', 'OBSERVE', 'The oracle node downloads every stored chunk, reads the database row and recomputes the Merkle root.'],
                            ['3', 'CALLBACK', 'It calls fulfillIntegrityCheck(requestId, root) from a separate wallet; only that wallet is allowed to.'],
                            ['4', 'JUDGE', 'The contract compares the root with the anchor, stores Healthy or Compromised and emits TamperAlarm on a mismatch.'],
                        ].map(([n, title, text]) => (
                            <div key={n} className="bg-white text-black border-4 border-black p-4">
                                <div className="flex items-center gap-2 mb-1">
                                    <div className="bg-brutal-yellow px-3 py-1 border-2 border-black font-black">{n}</div>
                                    <h3 className="font-black text-lg">{title}</h3>
                                </div>
                                <p className="font-mono text-sm">{text}</p>
                            </div>
                        ))}
                    </div>
                    <div className="bg-white text-black border-4 border-black p-4 mt-4 font-mono text-sm">
                        <strong>Design choices:</strong> the oracle reports but never decides; it uses a different
                        wallet from the anchorer so no single key can both write and vouch for a commitment; and if
                        storage is unreachable it stays silent and retries, because "could not look" is not
                        "found tampering".
                    </div>
                </Card>

                {/* Smart contract reference */}
                <Card className="bg-white border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-4 flex items-center gap-3">
                        <Anchor size={32} />
                        SMART CONTRACT REFERENCE
                    </h2>
                    <div className="overflow-x-auto border-4 border-black">
                        <table className="w-full font-mono text-xs">
                            <thead className="bg-black text-white">
                                <tr>
                                    <th className="p-2 text-left">FUNCTION</th>
                                    <th className="p-2 text-left">WHO</th>
                                    <th className="p-2 text-left">WHAT IT DOES</th>
                                </tr>
                            </thead>
                            <tbody>
                                {[
                                    ['anchorFile(fileId, root, manifest, chunks)', 'anchorer', 'Records a file commitment. Write-once: a second call reverts.'],
                                    ['revokeFile(fileId, reason)', 'anchorer', 'Flags a file as revoked; the anchor itself is never deleted.'],
                                    ['anchorCheckpoint(head, seq)', 'anchorer', 'Pins the audit-ledger head. seq must strictly increase.'],
                                    ['verifyFile(fileId, root)', 'anyone', 'Returns NotAnchored, Match, Mismatch, Revoked or Compromised.'],
                                    ['verifyChunk(fileId, hash, index, proof)', 'anyone', 'Verifies one chunk with a Merkle proof, on-chain.'],
                                    ['requestIntegrityCheck(fileId)', 'anchorer', 'Asks the oracle to check a file; emits IntegrityCheckRequested.'],
                                    ['fulfillIntegrityCheck(id, root)', 'oracle', 'Oracle callback; the contract judges and may emit TamperAlarm.'],
                                    ['getIntegrityReport(fileId)', 'anyone', 'Latest oracle verdict, wallet, block and number of checks.'],
                                    ['setAnchorer / setOracle', 'owner', 'Manages who may write anchors and who may report.'],
                                    ['transferOwnership(newOwner)', 'owner', 'Hands the owner role to another account.'],
                                ].map(([fn, who, what]) => (
                                    <tr key={fn} className="border-t-2 border-black align-top">
                                        <td className="p-2 font-bold">{fn}</td>
                                        <td className="p-2">{who}</td>
                                        <td className="p-2">{what}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <p className="font-mono text-xs mt-3">
                        Events: FileAnchored, FileRevoked, CheckpointAnchored, IntegrityCheckRequested,
                        IntegrityReported, TamperAlarm, AnchorerSet, OracleSet, OwnershipTransferred.
                        Merkle leaf = sha256(0x00 ‖ index ‖ chunkHash); node = sha256(0x01 ‖ min ‖ max).
                    </p>
                </Card>

                {/* Blockchain API */}
                <Card className="bg-brutal-bg border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-4 flex items-center gap-3">
                        <Server size={32} />
                        BLOCKCHAIN API
                    </h2>
                    <div className="space-y-2 font-mono text-sm">
                        {[
                            ['GET', '/chain/status', 'Network, contract, block height, bootstrap state'],
                            ['GET', '/chain/files/{id}/anchor', 'On-chain vs database comparison for one file'],
                            ['POST', '/chain/files/{id}/anchor', 'Admin: anchor a file uploaded before the chain existed'],
                            ['GET', '/chain/files/{id}/proof/{index}', 'Merkle proof for a single chunk, checked locally and on-chain'],
                            ['POST', '/chain/files/{id}/oracle-check', 'Request an oracle check and wait for the answer'],
                            ['GET', '/chain/oracle/status', 'Oracle wallet, stats and recent events'],
                            ['POST', '/admin/oracle/sweep', 'Admin: ask the oracle to re-check every file'],
                            ['GET', '/admin/ledger/verify', 'Admin: verify the hash chain and compare with the on-chain head'],
                            ['GET', '/admin/ledger/entries', 'Admin: recent ledger entries'],
                            ['POST', '/admin/ledger/checkpoint', 'Admin: pin the current ledger head on-chain'],
                        ].map(([method, path, text]) => (
                            <div key={method + path} className="bg-white border-4 border-black p-3 flex flex-wrap items-center gap-3">
                                <span className={`px-2 py-1 border-2 border-black font-black text-xs ${method === 'GET' ? 'bg-brutal-green' : 'bg-brutal-yellow'}`}>{method}</span>
                                <code className="font-bold">{path}</code>
                                <span className="text-xs">— {text}</span>
                            </div>
                        ))}
                    </div>
                </Card>

                {/* Known limitations */}
                <Card className="bg-brutal-yellow border-8 border-black p-8 mb-8">
                    <h2 className="text-3xl font-black mb-4 flex items-center gap-3 text-black">
                        <AlertTriangle size={32} />
                        KNOWN LIMITATIONS
                    </h2>
                    <ul className="font-mono text-sm text-black space-y-2 list-disc ml-5">
                        <li><strong>Local development chain.</strong> It lives in memory; state is rebuilt from the journal on each start. The same contract deploys unchanged to a public testnet.</li>
                        <li><strong>Single oracle.</strong> The observation is only as honest as the oracle (the "oracle problem"). Production systems use several oracles and require a quorum.</li>
                        <li><strong>Earlier files.</strong> Files uploaded before the blockchain layer show "not anchored" until an admin anchors them.</li>
                        <li><strong>Journal trust.</strong> Replay trusts the local journal. It is hash-chained so edits are detected, and replay stops at the first bad entry.</li>
                        <li><strong>Fail-open anchoring.</strong> If the chain is unreachable an upload still succeeds and is reported as not anchored, never silently verified.</li>
                    </ul>
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
                        <p>
                            <strong>✓ ANCHORED:</strong> File fingerprints live on a blockchain the
                            database owner cannot edit; only hashes are published, never data.
                        </p>
                        <p>
                            <strong>✓ MONITORED:</strong> An independent oracle re-checks stored files and
                            raises a permanent on-chain alarm on any mismatch.
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
