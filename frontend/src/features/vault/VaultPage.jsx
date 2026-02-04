import React, { useState, useEffect } from 'react';
import { Lock, Trash2, Key, RefreshCw } from 'lucide-react';
import { VaultDialog } from './VaultDialog';
import { listVaultKeys, deleteVaultKey } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';

export const VaultPage = ({ token }) => {
    const [vaultKeys, setVaultKeys] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showVaultDialog, setShowVaultDialog] = useState(false);
    const [selectedKey, setSelectedKey] = useState(null);

    const fetchVaultKeys = async () => {
        setLoading(true);
        setError('');
        try {
            const result = await listVaultKeys(token);
            setVaultKeys(result.keys || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchVaultKeys();
    }, [token]);

    const handleDeleteKey = async (vaultId) => {
        if (!confirm('Are you sure you want to delete this vault key? This action cannot be undone.')) {
            return;
        }

        try {
            await deleteVaultKey(vaultId, token);
            // Refresh list
            await fetchVaultKeys();
        } catch (err) {
            setError(err.message);
        }
    };

    const handleRetrieveKey = (hexKey) => {
        // Copy to clipboard
        navigator.clipboard.writeText(hexKey);
        alert(`Encryption key retrieved and copied to clipboard!\n\nKey: ${hexKey}`);
    };

    return (
        <div className="min-h-screen bg-brutal-bg p-8">
            <div className="max-w-6xl mx-auto">
                {/* Page Header */}
                <div className="mb-8 border-b-4 border-black pb-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="flex items-center gap-4 mb-2">
                                <Lock size={48} className="stroke-[3px]" />
                                <h1 className="text-5xl font-black">VAULT KEYS</h1>
                            </div>
                            <p className="font-mono text-lg ml-16">
                                Manage your encrypted vault keys
                            </p>
                        </div>
                        <div className="flex gap-3">
                            <Button
                                onClick={fetchVaultKeys}
                                className="bg-brutal-yellow hover:bg-yellow-400"
                            >
                                <RefreshCw size={18} className="inline mr-2" />
                                REFRESH
                            </Button>
                            <Button
                                onClick={() => setShowVaultDialog(true)}
                                className="bg-brutal-blue text-white hover:bg-blue-600"
                            >
                                <Key size={18} className="inline mr-2" />
                                RETRIEVE KEY
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="bg-brutal-pink text-white border-4 border-black p-4 mb-6 font-mono">
                        ❌ {error}
                    </div>
                )}

                {/* Loading State */}
                {loading ? (
                    <div className="text-center py-12">
                        <div className="font-mono text-2xl font-bold animate-pulse">
                            LOADING VAULT...
                        </div>
                    </div>
                ) : vaultKeys.length === 0 ? (
                    /* Empty State */
                    <Card className="bg-white border-8 border-black p-12 text-center">
                        <Lock size={80} className="mx-auto mb-6 stroke-[2px] text-gray-400" />
                        <h3 className="font-mono font-bold text-2xl mb-4">VAULT IS EMPTY</h3>
                        <p className="font-mono text-gray-600 mb-6">
                            No encryption keys stored yet. Upload a file with "Save to Vault" enabled.
                        </p>
                        <Button
                            onClick={() => window.location.href = '/upload'}
                            className="bg-brutal-blue text-white hover:bg-blue-600"
                        >
                            GO TO UPLOAD
                        </Button>
                    </Card>
                ) : (
                    /* Vault Keys Grid */
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {vaultKeys.map((key) => (
                            <Card key={key.vault_id} className="bg-white border-6 border-black p-6 hover:shadow-hard-sm transition-all">
                                {/* Key Label */}
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Key size={20} className="stroke-[3px]" />
                                            <h3 className="font-mono font-bold text-lg">{key.key_label}</h3>
                                        </div>
                                        <div className="text-xs font-mono text-gray-600 space-y-1">
                                            <div>Vault ID: {key.vault_id.slice(0, 16)}...</div>
                                            {key.file_id && (
                                                <div>File ID: {key.file_id.slice(0, 16)}...</div>
                                            )}
                                            <div>Created: {new Date(key.created_at).toLocaleString()}</div>
                                        </div>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex gap-3 mt-4 pt-4 border-t-4 border-black">
                                    <Button
                                        onClick={() => {
                                            setSelectedKey(key);
                                            setShowVaultDialog(true);
                                        }}
                                        className="flex-1 bg-brutal-blue text-white hover:bg-blue-600"
                                    >
                                        <Key size={16} className="inline mr-2" />
                                        RETRIEVE
                                    </Button>
                                    <Button
                                        onClick={() => handleDeleteKey(key.vault_id)}
                                        className="bg-brutal-pink text-white hover:bg-pink-600"
                                    >
                                        <Trash2 size={16} />
                                    </Button>
                                </div>
                            </Card>
                        ))}
                    </div>
                )}

                {/* Info Cards */}
                <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-brutal-yellow border-4 border-black p-4">
                        <h4 className="font-mono font-bold mb-2">🔐 SECURE STORAGE</h4>
                        <p className="text-sm font-mono">Keys are encrypted with your vault password</p>
                    </div>
                    <div className="bg-brutal-blue text-white border-4 border-black p-4">
                        <h4 className="font-mono font-bold mb-2">🔑 MFA PROTECTED</h4>
                        <p className="text-sm font-mono">Requires MFA code for key retrieval</p>
                    </div>
                    <div className="bg-brutal-pink text-white border-4 border-black p-4">
                        <h4 className="font-mono font-bold mb-2">🗑️ FULL CONTROL</h4>
                        <p className="text-sm font-mono">Delete keys anytime without affecting files</p>
                    </div>
                </div>
            </div>

            {/* Vault Dialog */}
            {showVaultDialog && (
                <VaultDialog
                    onRetrieve={handleRetrieveKey}
                    onClose={() => {
                        setShowVaultDialog(false);
                        setSelectedKey(null);
                    }}
                    vaultKeys={vaultKeys}
                    token={token}
                    onRefresh={fetchVaultKeys}
                />
            )}
        </div>
    );
};
