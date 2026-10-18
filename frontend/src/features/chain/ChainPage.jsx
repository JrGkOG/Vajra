import React, { useState, useEffect, useCallback } from 'react';
import { Link2, ShieldCheck, ShieldAlert, RefreshCw, Anchor, Hash } from 'lucide-react';
import {
    getChainStatus, verifyLedger, getLedgerEntries, anchorLedgerCheckpoint,
    getOracleStatus, runOracleSweep
} from '../../services/api';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

const short = (h, n = 10) => (h ? `${h.slice(0, n)}…${h.slice(-6)}` : '—');

const Stat = ({ label, value, mono = true }) => (
    <div className="border-4 border-black p-3 bg-white">
        <div className="text-xs font-bold uppercase text-gray-600">{label}</div>
        <div className={`text-sm font-bold break-all ${mono ? 'font-mono' : ''}`}>{value ?? '—'}</div>
    </div>
);

export const ChainPage = ({ token, user }) => {
    const isAdmin = user?.permissions?.can_view_all_logs || user?.role === 'admin';

    const [status, setStatus] = useState(null);
    const [statusError, setStatusError] = useState('');
    const [ledger, setLedger] = useState(null);
    const [entries, setEntries] = useState([]);
    const [oracle, setOracle] = useState(null);
    const [busy, setBusy] = useState('');
    const [notice, setNotice] = useState(null);

    const loadStatus = useCallback(async () => {
        try {
            setStatus(await getChainStatus(token));
            setStatusError('');
        } catch (e) {
            setStatusError(e.message);
        }
    }, [token]);

    const loadEntries = useCallback(async () => {
        if (!isAdmin) return;
        try {
            setEntries((await getLedgerEntries(token, 15)).entries || []);
        } catch { /* ledger table may not exist yet */ }
    }, [token, isAdmin]);

    const loadOracle = useCallback(async () => {
        try {
            setOracle(await getOracleStatus(token));
        } catch { /* chain offline — the network card already explains it */ }
    }, [token]);

    useEffect(() => {
        loadStatus();
        loadEntries();
        loadOracle();
        const t = setInterval(() => { loadStatus(); loadOracle(); }, 5000);
        return () => clearInterval(t);
    }, [loadStatus, loadEntries, loadOracle]);

    const run = async (name, fn) => {
        setBusy(name);
        setNotice(null);
        try {
            await fn();
        } catch (e) {
            setNotice({ kind: 'error', text: e.message });
        } finally {
            setBusy('');
        }
    };

    const doVerify = () => run('verify', async () => {
        setLedger(await verifyLedger(token));
        await loadEntries();
    });

    const doSweep = () => run('sweep', async () => {
        const r = await runOracleSweep(token);
        setNotice({ kind: 'ok', text: `Oracle asked to re-check ${r.requested} file(s). Answers appear below within seconds.` });
        setTimeout(loadOracle, 2500);
    });

    const doCheckpoint = () => run('checkpoint', async () => {
        const r = await anchorLedgerCheckpoint(token);
        setNotice({
            kind: 'ok',
            text: `Ledger head anchored: entries 1–${r.seq} in block #${r.block_number} · tx ${short(r.tx_hash, 14)}`
        });
        await loadStatus();
        setLedger(await verifyLedger(token));
    });

    const connected = status?.connected;

    return (
        <div className="min-h-screen bg-brutal-bg p-8">
            <div className="max-w-7xl mx-auto space-y-8">
                <div className="flex items-center gap-3">
                    <Link2 size={36} />
                    <div>
                        <h1 className="text-4xl">BLOCKCHAIN LAYER</h1>
                        <p className="font-mono text-sm">
                            Files stay in the database. Their fingerprints live on-chain, where the database owner cannot edit them.
                        </p>
                    </div>
                </div>

                {notice && (
                    <div className={`border-4 p-3 font-mono font-bold ${notice.kind === 'ok'
                        ? 'border-green-600 bg-green-50 text-green-800'
                        : 'border-red-600 bg-red-50 text-red-800'}`}>
                        {notice.text}
                    </div>
                )}

                {/* ── Network ───────────────────────────────── */}
                <Card title="NETWORK">
                    <div className="flex items-center justify-between mb-4">
                        <div className={`inline-flex items-center gap-2 border-4 border-black px-3 py-1 font-mono font-bold ${connected ? 'bg-brutal-green' : 'bg-brutal-pink text-white'}`}>
                            <span className={`w-3 h-3 border-2 border-black ${connected ? 'bg-black' : 'bg-white'}`} />
                            {connected ? 'CONNECTED' : 'OFFLINE'}
                        </div>
                        <Button onClick={loadStatus} className="bg-white !px-4 !py-2">
                            <RefreshCw size={16} />
                        </Button>
                    </div>

                    {statusError && <div className="font-mono text-red-700">{statusError}</div>}
                    {status && !connected && (
                        <div className="font-mono text-sm border-4 border-black bg-yellow-50 p-3">
                            {status.reason}
                            <div className="mt-2 text-xs">
                                Uploads still work; files are marked “not anchored” until the chain is back.
                            </div>
                        </div>
                    )}
                    {status?.bootstrap && status.bootstrap.phase !== 'idle' && (
                        <div className={`mb-4 border-4 border-black p-3 font-mono text-sm ${status.bootstrap.phase === 'ready' ? 'bg-green-50'
                            : status.bootstrap.phase === 'failed' ? 'bg-red-50' : 'bg-yellow-50'}`}>
                            <div className="font-bold">
                                AUTO-START: {status.bootstrap.phase.toUpperCase().replace('_', ' ')}
                            </div>
                            <div>{status.bootstrap.message}</div>
                            {status.bootstrap.replay && (
                                <div className="text-xs mt-1">
                                    Restored from journal: {status.bootstrap.replay.files_replayed} file(s),{' '}
                                    {status.bootstrap.replay.checkpoints_replayed} checkpoint(s)
                                    {status.bootstrap.replay.journal_error && (
                                        <span className="text-red-700 font-bold"> · ⚠️ journal: {status.bootstrap.replay.journal_error}</span>
                                    )}
                                </div>
                            )}
                            {status.bootstrap.drift?.length > 0 && (
                                <div className="mt-2 text-xs text-red-800 font-bold">
                                    ⚠️ {status.bootstrap.drift.length} file(s) differ from what was anchored:
                                    {status.bootstrap.drift.slice(0, 3).map((d) => (
                                        <div key={d.file_id}>• {d.file_id.slice(0, 8)}… {d.reason}</div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                    {connected && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <Stat label="Network" value={`${status.network} · chain ${status.chain_id}`} />
                            <Stat label="Latest block" value={`#${status.block_number}`} />
                            <Stat label="Files anchored" value={status.total_files_anchored} />
                            <Stat label="Checkpoints" value={status.checkpoint_count} />
                            <div className="md:col-span-2"><Stat label="Contract (VajraRegistry)" value={status.contract_address} /></div>
                            <div className="md:col-span-2"><Stat label="Anchoring wallet" value={status.signer} /></div>
                        </div>
                    )}
                </Card>

                {/* ── Audit ledger ──────────────────────────── */}
                <Card title="AUDIT LEDGER (HASH CHAIN)">
                    {!isAdmin ? (
                        <div className="font-mono">Admin access required to inspect the audit ledger.</div>
                    ) : (
                        <>
                            <p className="font-mono text-sm mb-4">
                                Every log entry is sealed with <b>SHA-256(previous hash ‖ entry)</b>. Changing or deleting
                                one row breaks every hash after it. Pinning the head on-chain stops someone recomputing the whole chain.
                            </p>

                            <div className="flex flex-wrap gap-3 mb-6">
                                <Button onClick={doVerify} disabled={!!busy} className="bg-brutal-yellow">
                                    <span className="inline-flex items-center gap-2">
                                        <ShieldCheck size={18} />
                                        {busy === 'verify' ? 'VERIFYING…' : 'VERIFY LEDGER'}
                                    </span>
                                </Button>
                                <Button onClick={doCheckpoint} disabled={!!busy || !connected} className="bg-brutal-blue text-white">
                                    <span className="inline-flex items-center gap-2">
                                        <Anchor size={18} />
                                        {busy === 'checkpoint' ? 'ANCHORING…' : 'ANCHOR HEAD ON-CHAIN'}
                                    </span>
                                </Button>
                            </div>

                            {ledger && (
                                <div className={`border-4 p-4 mb-6 font-mono ${ledger.valid ? 'border-green-600 bg-green-50' : 'border-red-600 bg-red-50'}`}>
                                    <div className="flex items-center gap-2 font-bold text-lg mb-2">
                                        {ledger.valid ? <ShieldCheck className="text-green-700" /> : <ShieldAlert className="text-red-700" />}
                                        {ledger.valid ? 'LEDGER INTACT' : 'TAMPERING DETECTED'}
                                    </div>
                                    <div className="text-sm space-y-1">
                                        <div>Entries: {ledger.total_entries} · head {short(ledger.head)}</div>
                                        {!ledger.valid && (
                                            <div className="text-red-800 font-bold">
                                                {ledger.reason}{ledger.seq ? ` (entry #${ledger.seq})` : ''}
                                            </div>
                                        )}
                                        {ledger.anchor?.checked ? (
                                            <div>
                                                On-chain checkpoint at entry #{ledger.anchor.checkpoint_seq} (block #{ledger.anchor.block_number}):{' '}
                                                {ledger.anchor.consistent ? '✅ consistent' : '❌ MISMATCH'}
                                                {' · '}{ledger.anchor.entries_since_checkpoint} newer entries not yet anchored
                                            </div>
                                        ) : (
                                            <div>{ledger.anchor?.note || 'No on-chain checkpoint compared.'}</div>
                                        )}
                                        {!ledger.chain_reachable && <div>⚠️ Chain unreachable — only internal consistency was checked.</div>}
                                    </div>
                                </div>
                            )}

                            <div className="overflow-x-auto border-4 border-black bg-white">
                                <table className="w-full font-mono text-xs">
                                    <thead className="bg-black text-white">
                                        <tr>
                                            <th className="p-2 text-left">#</th>
                                            <th className="p-2 text-left">ACTION</th>
                                            <th className="p-2 text-left">SOURCE</th>
                                            <th className="p-2 text-left"><Hash size={12} className="inline" /> PREV</th>
                                            <th className="p-2 text-left"><Hash size={12} className="inline" /> ENTRY HASH</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {entries.length === 0 && (
                                            <tr><td colSpan={5} className="p-3">No ledger entries yet — perform an action, or run create_ledger_table.sql.</td></tr>
                                        )}
                                        {entries.map((e) => (
                                            <tr key={e.seq} className="border-t-2 border-black">
                                                <td className="p-2 font-bold">{e.seq}</td>
                                                <td className="p-2">{e.entry?.action}</td>
                                                <td className="p-2">{e.entry?.source}</td>
                                                <td className="p-2">{short(e.prev_hash, 8)}</td>
                                                <td className="p-2">{short(e.entry_hash, 8)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </>
                    )}
                </Card>

                {/* ── Oracle ────────────────────────────────── */}
                <Card title="ORACLE (OFF-CHAIN → ON-CHAIN)">
                    <p className="font-mono text-sm mb-4">
                        A contract cannot read the database or storage. The <b>oracle</b> is a separate wallet that
                        watches for check requests, inspects the real stored chunks, and reports what it saw. The
                        contract itself compares that with the anchor and raises a <b>TamperAlarm</b> if they differ.
                    </p>

                    {oracle && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                            <div className="md:col-span-2"><Stat label="Oracle wallet (≠ anchoring wallet)" value={oracle.oracle_address} /></div>
                            <Stat label="Authorised on-chain" value={oracle.authorised ? 'YES' : 'NO'} />
                            <Stat label="Auto sweep" value={oracle.sweep_seconds > 0 ? `every ${oracle.sweep_seconds}s` : 'off'} />
                            <Stat label="Requests seen" value={oracle.stats?.requests_seen} />
                            <Stat label="Reports sent" value={oracle.stats?.reports_sent} />
                            <Stat label="Skipped (data unreachable)" value={oracle.stats?.unavailable_skips} />
                            <Stat label="Node" value={oracle.stats?.running ? 'RUNNING' : 'STOPPED'} />
                        </div>
                    )}

                    {isAdmin && (
                        <div className="mb-4">
                            <Button onClick={doSweep} disabled={!!busy || !connected} className="bg-brutal-purple text-white">
                                {busy === 'sweep' ? 'REQUESTING…' : 'RUN ORACLE CHECK ON ALL FILES'}
                            </Button>
                        </div>
                    )}

                    <div className="overflow-x-auto border-4 border-black bg-white">
                        <table className="w-full font-mono text-xs">
                            <thead className="bg-black text-white">
                                <tr>
                                    <th className="p-2 text-left">BLOCK</th>
                                    <th className="p-2 text-left">EVENT</th>
                                    <th className="p-2 text-left">REQ</th>
                                    <th className="p-2 text-left">FILE (HASHED ID)</th>
                                    <th className="p-2 text-left">RESULT</th>
                                </tr>
                            </thead>
                            <tbody>
                                {(!oracle || oracle.events.length === 0) && (
                                    <tr><td colSpan={5} className="p-3">No oracle activity yet.</td></tr>
                                )}
                                {oracle?.events.map((e, i) => (
                                    <tr key={`${e.block}-${e.index}-${i}`}
                                        className={`border-t-2 border-black ${e.type === 'TamperAlarm' ? 'bg-red-100' : ''}`}>
                                        <td className="p-2 font-bold">#{e.block}</td>
                                        <td className="p-2">{e.type === 'TamperAlarm' ? '🚨 TamperAlarm' : e.type.replace('IntegrityCheck', 'Check ').replace('IntegrityReported', 'Reported')}</td>
                                        <td className="p-2">{e.request_id ?? '—'}</td>
                                        <td className="p-2">{short(e.file_key, 8)}</td>
                                        <td className="p-2">
                                            {e.status === 'HEALTHY' && '✅ healthy'}
                                            {e.status === 'COMPROMISED' && '🚨 compromised'}
                                            {e.type === 'TamperAlarm' && `saw ${short(e.observed_root, 6)}`}
                                            {e.type === 'IntegrityCheckRequested' && 'awaiting oracle'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>

                {/* ── Concepts ──────────────────────────────── */}
                <Card title="WHAT IS ON-CHAIN, AND WHAT IS NOT">
                    <div className="grid md:grid-cols-2 gap-4 font-mono text-sm">
                        <div className="border-4 border-black bg-green-50 p-4">
                            <div className="font-bold mb-2">ON-CHAIN (public, permanent)</div>
                            <ul className="list-disc ml-5 space-y-1">
                                <li>Merkle root of each file’s encrypted chunk hashes</li>
                                <li>Hash of the signed file manifest</li>
                                <li>SHA-256 of the file id (not the id itself)</li>
                                <li>Periodic head of the audit hash-chain</li>
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
            </div>
        </div>
    );
};
