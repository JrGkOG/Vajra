import React, { useState, useEffect } from 'react';
import { X, Lock, Mail } from 'lucide-react';

export const VaultDialog = ({ onRetrieve, onClose, vaultKeys, token, onRefresh }) => {
    const [selectedVaultId, setSelectedVaultId] = useState('');
    const [password, setPassword] = useState('');
    const [mfaCode, setMfaCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [sendingMFA, setSendingMFA] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [localKeys, setLocalKeys] = useState(vaultKeys);

    // Update local keys when prop changes
    useEffect(() => {
        console.log('🔍 VaultDialog: Received vault keys:', vaultKeys);
        console.log('🔍 VaultDialog: Number of keys:', vaultKeys?.length);
        setLocalKeys(vaultKeys);
    }, [vaultKeys]);

    const handleSendMFA = async () => {
        setError('');
        setSuccessMessage('');
        setSendingMFA(true);

        try {
            const { sendVaultMFA } = await import('../../services/api');
            const result = await sendVaultMFA(token, 'vault_retrieve');

            console.log('✅ MFA code sent for vault retrieval');
            setSuccessMessage(`Code sent to ${result.email}`);
        } catch (err) {
            setError(err.message);
        } finally {
            setSendingMFA(false);
        }
    };

    const handleRetrieve = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const { retrieveKeyFromVault } = await import('../../services/api');
            const result = await retrieveKeyFromVault(selectedVaultId, password, mfaCode, token);

            // Call parent callback with retrieved hex key
            onRetrieve(result.hex_key);
            onClose();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white border-8 border-black shadow-hard-xl max-w-md w-full p-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <Lock size={32} className="stroke-[3px]" />
                        <h2 className="text-2xl font-black">RETRIEVE KEY</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 border-4 border-black"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="bg-brutal-pink text-white border-6 border-black p-4 mb-6 font-mono shadow-hard-sm">
                        <p className="font-bold">⚠️ {error}</p>
                    </div>
                )}

                {/* Success Message */}
                {successMessage && (
                    <div className="bg-brutal-green text-white border-6 border-black p-4 mb-6 font-mono shadow-hard-sm">
                        <p className="font-bold">✅ {successMessage}</p>
                        <p className="text-sm mt-1">Check your email for the 6-digit code</p>
                    </div>
                )}

                <form onSubmit={handleRetrieve} className="space-y-6">
                    {/* Select Vault Key */}
                    <div>
                        <label className="block font-mono font-bold text-lg mb-2">
                            SELECT KEY {localKeys.length > 0 && `(${localKeys.length} available)`}
                        </label>
                        <select
                            value={selectedVaultId}
                            onChange={(e) => setSelectedVaultId(e.target.value)}
                            required
                            className="w-full p-4 border-6 border-black shadow-hard-sm focus:outline-none focus:shadow-hard transition-all font-mono text-sm"
                        >
                            <option value="">
                                {localKeys.length === 0 ? '-- No keys in vault yet --' : '-- Choose a key --'}
                            </option>
                            {localKeys.map((key) => (
                                <option key={key.vault_id} value={key.vault_id}>
                                    {key.key_label} | File: {key.file_id ? key.file_id.slice(0, 13) : 'N/A'}...
                                </option>
                            ))}
                        </select>
                        {localKeys.length === 0 && (
                            <p className="text-xs font-mono text-gray-600 mt-2">
                                💡 Upload a file with "Save to vault" enabled to store keys
                            </p>
                        )}
                    </div>

                    {/* Password */}
                    <div>
                        <label className="block font-mono font-bold text-lg mb-2">VAULT PASSWORD</label>
                        <input
                            type="password"
                            placeholder="Enter vault password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className="w-full p-4 border-6 border-black shadow-hard-sm focus:outline-none focus:shadow-hard transition-all font-mono"
                        />
                    </div>

                    {/* MFA Code Section */}
                    <div>
                        <label className="block font-mono font-bold text-lg mb-2">MFA CODE</label>

                        {/* Send MFA Button */}
                        <button
                            type="button"
                            onClick={handleSendMFA}
                            disabled={sendingMFA}
                            className="w-full brutal-btn bg-brutal-yellow text-black py-3 mb-3 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            <Mail size={20} className="stroke-[3px]" />
                            {sendingMFA ? 'SENDING CODE...' : 'SEND MFA CODE TO EMAIL'}
                        </button>

                        {/* MFA Input */}
                        <input
                            type="text"
                            placeholder="000000"
                            value={mfaCode}
                            onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                            required
                            maxLength={6}
                            className="w-full p-4 border-6 border-black shadow-hard-sm focus:outline-none focus:shadow-hard transition-all font-mono text-xl text-center tracking-widest"
                        />
                    </div>

                    {/* Buttons */}
                    <div className="flex gap-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 brutal-btn bg-white text-black py-4"
                        >
                            CANCEL
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 brutal-btn bg-brutal-blue text-white py-4 disabled:opacity-50"
                        >
                            {loading ? 'RETRIEVING...' : 'RETRIEVE'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
