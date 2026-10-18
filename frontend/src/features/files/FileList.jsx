import React, { useEffect, useRef, useState } from 'react';
import { Download, Lock, RefreshCw, Key, Shield, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { getFiles, downloadFile, listVaultKeys, verifyFileIntegrity } from '../../services/api';
import { VaultDialog } from '../vault/VaultDialog';
import { parseKeyFile } from '../../utils/keyFile';

const ClassificationBadge = ({ level }) => {
    const styles = {
        top_secret: 'bg-red-500 text-white',
        mission_logs: 'bg-yellow-400 text-black',
        public: 'bg-green-400 text-black'
    };

    return (
        <span className={`border-2 border-black px-2 py-0.5 text-xs font-bold uppercase ${styles[level] || 'bg-gray-200'}`}>
            {level.replace('_', ' ')}
        </span>
    );
};

const SignatureBadge = ({ file }) => {
    const isSigned = file.file_signature && file.chunk_signatures && file.chunk_signatures.length > 0;

    if (isSigned) {
        return (
            <div className="flex items-center gap-1" title={`Signed by ${file.signed_by_user_id || 'unknown'}`}>
                <span className="text-green-600 font-bold">✓</span>
                <span className="text-xs">SIGNED</span>
            </div>
        );
    }

    return (
        <div className="flex items-center gap-1">
            <span className="text-gray-400">⚠</span>
            <span className="text-xs text-gray-500">UNSIGNED</span>
        </div>
    );
};

export const FileList = ({ token }) => {
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [downloadingId, setDownloadingId] = useState(null);
    const [showVaultDialog, setShowVaultDialog] = useState(false);
    const [vaultKeys, setVaultKeys] = useState([]);
    const [currentFileForDownload, setCurrentFileForDownload] = useState(null);
    const [integrityResult, setIntegrityResult] = useState(null);
    const [checkingIntegrity, setCheckingIntegrity] = useState(null);

    // Pagination state
    const [currentPage, setCurrentPage] = useState(1);
    const FILES_PER_PAGE = 10;

    // Calculate pagination
    const totalPages = Math.ceil(files.length / FILES_PER_PAGE);
    const startIndex = (currentPage - 1) * FILES_PER_PAGE;
    const endIndex = startIndex + FILES_PER_PAGE;
    const paginatedFiles = files.slice(startIndex, endIndex);

    const fetchFiles = async () => {
        if (!token) return;

        setLoading(true);
        setError('');

        try {
            const response = await getFiles(token);
            setFiles(response.files || []);
            setCurrentPage(1); // Reset to first page on refresh
        } catch (err) {
            setError(err.message || 'Failed to fetch files');
        } finally {
            setLoading(false);
        }
    };

    const fetchVaultKeys = async () => {
        try {
            const response = await listVaultKeys(token);
            console.log('🔍 DEBUG: Vault keys response:', response);
            console.log('🔍 DEBUG: Number of keys:', response.keys?.length);
            setVaultKeys(response.keys || []);
        } catch (err) {
            console.error('Failed to fetch vault keys:', err);
        }
    };

    useEffect(() => {
        fetchFiles();
        fetchVaultKeys();
    }, [token]);

    // Manual download: the user selects the key file saved at upload time.
    const keyInputRef = useRef(null);
    const pendingFileRef = useRef(null);

    const handleDownload = (file) => {
        pendingFileRef.current = file;
        if (keyInputRef.current) {
            keyInputRef.current.value = '';      // allow re-selecting the same file
            keyInputRef.current.click();
        }
    };

    const handleKeyFileChosen = async (e) => {
        const keyFile = e.target.files && e.target.files[0];
        const file = pendingFileRef.current;
        if (!keyFile || !file) return;

        let parsed;
        try {
            parsed = parseKeyFile(await keyFile.text());
        } catch {
            parsed = null;
        }
        if (!parsed) {
            alert('That file does not contain an encryption key. Select the vajra-key-XXXX.txt saved at upload.');
            return;
        }
        if (parsed.fileId && parsed.fileId !== file.file_id) {
            alert(`This key file belongs to a different file.\n\nSelected file: ${file.filename}\nKey file is for ID: ${parsed.fileId}`);
            return;
        }
        await runDownload(file, parsed.key);
    };

    const runDownload = async (file, encryptionKey) => {
        setDownloadingId(file.file_id);
        try {
            const blob = await downloadFile(file.file_id, encryptionKey, token);

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            alert(`Download failed: ${err.message}`);
        } finally {
            setDownloadingId(null);
        }
    };

    const handleVaultDownload = async (file) => {
        setCurrentFileForDownload(file);
        // Refresh vault keys before showing dialog
        await fetchVaultKeys();
        setShowVaultDialog(true);
    };

    const handleVaultKeyRetrieved = async (hexKey) => {
        if (!currentFileForDownload) return;

        setDownloadingId(currentFileForDownload.file_id);
        try {
            const blob = await downloadFile(currentFileForDownload.file_id, hexKey, token);

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentFileForDownload.filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            alert(`Download failed: ${err.message}`);
        } finally {
            setDownloadingId(null);
            setCurrentFileForDownload(null);
        }
    };

    const handleCheckIntegrity = async (file) => {
        setCheckingIntegrity(file.file_id);
        setIntegrityResult(null);

        try {
            const result = await verifyFileIntegrity(file.file_id, token);
            setIntegrityResult(result);
        } catch (err) {
            setIntegrityResult({
                integrity_status: 'ERROR',
                error: err.message
            });
        } finally {
            setCheckingIntegrity(null);
        }
    };

    if (loading) {
        return (
            <div className="text-center p-12 font-mono">
                <RefreshCw className="animate-spin inline-block mb-4" size={32} />
                <p>LOADING SECURE VAULT...</p>
            </div>
        );
    }

    return (
        <div>
            {/* Hidden picker for manual-mode key files (opened by the DL button) */}
            <input
                ref={keyInputRef}
                type="file"
                accept=".txt,text/plain"
                className="hidden"
                onChange={handleKeyFileChosen}
            />
            <div className="flex justify-between items-end mb-4">
                <h3 className="text-xl font-mono font-bold">SECURE VAULT</h3>
                <div className="flex gap-2 items-center">
                    <span className="text-xs bg-black text-white px-2 py-1">TOTAL: {files.length} FILES</span>
                    <Button onClick={fetchFiles} className="text-xs py-1 px-2">
                        <RefreshCw size={14} className="inline mr-1" /> REFRESH
                    </Button>
                </div>
            </div>

            {error && (
                <div className="mb-4 bg-red-100 border-4 border-red-600 p-4 font-mono text-sm">
                    ❌ {error}
                </div>
            )}

            {files.length === 0 ? (
                <div className="bg-white border-4 border-black p-12 text-center font-mono">
                    <p className="text-lg font-bold">NO FILES IN VAULT</p>
                    <p className="text-sm mt-2">Upload a file to get started</p>
                </div>
            ) : (
                <>
                    <div className="overflow-x-auto border-4 border-black shadow-hard">
                        <table className="w-full text-left font-mono">
                            <thead className="bg-brutal-bg border-b-4 border-black">
                                <tr>
                                    <th className="p-4 border-r-4 border-black">FILENAME</th>
                                    <th className="p-4 border-r-4 border-black">CLASS</th>
                                    <th className="p-4 border-r-4 border-black">CHUNKS</th>
                                    <th className="p-4 border-r-4 border-black">OWNER</th>
                                    <th className="p-4">ACTION</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white">
                                {paginatedFiles.map((file, idx) => (
                                    <tr key={file.file_id} className={idx !== paginatedFiles.length - 1 ? 'border-b-4 border-black' : ''}>
                                        <td className="p-4 border-r-4 border-black font-bold flex items-center gap-2">
                                            <Lock size={16} /> {file.filename}
                                        </td>
                                        <td className="p-4 border-r-4 border-black">
                                            <ClassificationBadge level={file.classification || 'public'} />
                                        </td>
                                        <td className="p-4 border-r-4 border-black text-sm">{file.total_chunks}</td>
                                        <td className="p-4 border-r-4 border-black text-sm">{file.owner_id}</td>
                                        <td className="p-4">
                                            <div className="flex gap-1 flex-nowrap">
                                                <Button
                                                    onClick={() => handleCheckIntegrity(file)}
                                                    disabled={checkingIntegrity === file.file_id}
                                                    className="py-1 px-2 text-xs flex items-center gap-1 bg-green-500 text-white hover:bg-green-600 border-4 border-black whitespace-nowrap"
                                                    title="Verify file integrity"
                                                >
                                                    <Shield size={14} />
                                                    {checkingIntegrity === file.file_id ? 'CHECKING...' : 'CHECK'}
                                                </Button>
                                                <Button
                                                    onClick={() => handleVaultDownload(file)}
                                                    disabled={downloadingId === file.file_id}
                                                    className="py-1 px-2 text-xs flex items-center gap-1 bg-brutal-yellow text-black hover:bg-yellow-500 border-4 border-black whitespace-nowrap"
                                                >
                                                    <Key size={14} />
                                                    KEY
                                                </Button>
                                                <Button
                                                    onClick={() => handleDownload(file)}
                                                    disabled={downloadingId === file.file_id}
                                                    className="py-1 px-2 text-xs flex items-center gap-1 bg-brutal-blue text-white hover:bg-blue-600 border-4 border-black whitespace-nowrap"
                                                >
                                                    <Download size={14} />
                                                    {downloadingId === file.file_id ? 'DOWNLOADING...' : 'DL'}
                                                </Button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination Controls */}
                    {totalPages > 1 && (
                        <div className="flex justify-between items-center mt-4 p-4 bg-white border-4 border-black">
                            <Button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="py-2 px-4 text-sm font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                ← PREV
                            </Button>

                            <div className="font-mono text-sm">
                                <span className="font-bold">PAGE {currentPage}</span> of {totalPages}
                                <span className="ml-4 text-gray-600">
                                    (Showing {startIndex + 1}-{Math.min(endIndex, files.length)} of {files.length})
                                </span>
                            </div>

                            <Button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="py-2 px-4 text-sm font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                NEXT →
                            </Button>
                        </div>
                    )}
                </>
            )}

            {/* Vault Dialog */}
            {showVaultDialog && (
                <VaultDialog
                    onRetrieve={handleVaultKeyRetrieved}
                    onClose={() => {
                        setShowVaultDialog(false);
                        setCurrentFileForDownload(null);
                    }}
                    vaultKeys={vaultKeys}
                    token={token}
                />
            )}

            {/* Integrity Check Result Modal */}
            {integrityResult && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white border-4 border-black shadow-hard max-w-2xl w-full max-h-[80vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-xl font-mono font-bold">
                                    🔒 INTEGRITY CHECK RESULTS
                                </h3>
                                <button
                                    onClick={() => setIntegrityResult(null)}
                                    className="text-2xl font-bold hover:bg-gray-100 px-2"
                                >
                                    ×
                                </button>
                            </div>

                            <div className="space-y-4">
                                {/* Overall Status */}
                                <div className={`border-4 p-4 font-mono ${integrityResult.integrity_status === 'VERIFIED'
                                    ? 'border-green-600 bg-green-50'
                                    : integrityResult.integrity_status === 'COMPROMISED'
                                        ? 'border-red-600 bg-red-50'
                                        : 'border-yellow-600 bg-yellow-50'
                                    }`}>
                                    <div className="flex items-center gap-2 mb-2">
                                        {integrityResult.integrity_status === 'VERIFIED' ? (
                                            <CheckCircle className="text-green-600" size={24} />
                                        ) : (
                                            <XCircle className="text-red-600" size={24} />
                                        )}
                                        <span className="font-bold text-lg">
                                            {integrityResult.integrity_status}
                                        </span>
                                    </div>
                                    <div className="text-sm">
                                        <div>File: {integrityResult.filename}</div>
                                        <div>Chunks: {integrityResult.total_chunks}</div>
                                        <div>Signed: {integrityResult.is_signed ? 'YES' : 'NO'}</div>
                                        {integrityResult.signed_by && (
                                            <div>Signed by: {integrityResult.signed_by}</div>
                                        )}
                                    </div>
                                </div>

                                {/* Checks */}
                                {integrityResult.checks?.map((check, idx) => (
                                    <div key={idx} className="border-2 border-black p-3">
                                        <div className="font-bold mb-2">{check.type.toUpperCase().replace('_', ' ')}</div>
                                        <div className="text-sm">
                                            {check.status && (
                                                <div className={
                                                    check.status === 'PASS' ? 'text-green-600'
                                                        : check.status === 'WARN' ? 'text-yellow-700'
                                                            : 'text-red-600'
                                                }>
                                                    {check.status}: {check.message}
                                                </div>
                                            )}
                                            {check.type === 'blockchain_anchor' && check.anchored && (
                                                <div className="mt-2 text-xs space-y-1 break-all bg-gray-50 border-2 border-black p-2">
                                                    <div>Block: #{check.block_number} (chain {check.chain_id})</div>
                                                    <div>Contract: {check.contract_address}</div>
                                                    {check.tx_hash && <div>Tx: {check.tx_hash}</div>}
                                                    <div>On-chain root: {check.on_chain_root}</div>
                                                    <div>Database root: {check.local_root}</div>
                                                    {check.oracle && check.oracle.checks > 0 && (
                                                        <div>
                                                            Oracle: {check.oracle.status === 'HEALTHY' ? '✅ HEALTHY' : '🚨 COMPROMISED'}
                                                            {' '}(block #{check.oracle.block_number}, {check.oracle.checks} check
                                                            {check.oracle.checks === 1 ? '' : 's'})
                                                        </div>
                                                    )}
                                                    <div>
                                                        Root {check.root_match ? '✅ match' : '❌ MISMATCH'}
                                                        {' · '}
                                                        Manifest {check.manifest_match ? '✅ match' : '❌ MISMATCH'}
                                                    </div>
                                                </div>
                                            )}
                                            {check.chunks && (
                                                <div className="mt-2">
                                                    {check.chunks.slice(0, 5).map((chunk, cidx) => (
                                                        <div key={cidx} className="text-xs mb-1">
                                                            Chunk {chunk.chunk_index}:
                                                            {chunk.status === 'PASS' ? ' ✅ OK' : ` ❌ ${chunk.error}`}
                                                        </div>
                                                    ))}
                                                    {check.chunks.length > 5 && (
                                                        <div className="text-xs">+ {check.chunks.length - 5} more chunks</div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}

                                {/* Safe to Download */}
                                <div className="text-center font-mono font-bold text-lg">
                                    {integrityResult.safe_to_download ? (
                                        <div className="text-green-600">✅ SAFE TO DOWNLOAD</div>
                                    ) : (
                                        <div className="text-red-600">🚫 DO NOT DOWNLOAD - COMPROMISED</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

