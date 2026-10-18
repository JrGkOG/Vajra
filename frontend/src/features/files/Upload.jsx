import React, { useState } from 'react';
import { UploadCloud } from 'lucide-react';
import { uploadFile, storeKeyInVault } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { nextKeyNumber, buildKeyFile, keyFileName, downloadTextFile } from '../../utils/keyFile';

export const Upload = ({ token }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [file, setFile] = useState(null);
    const [classification, setClassification] = useState('public');
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);
    const [error, setError] = useState('');

    // Vault options
    const [saveToVault, setSaveToVault] = useState(true); // Default to true
    const [vaultPassword, setVaultPassword] = useState('');
    const [keyLabel, setKeyLabel] = useState('');

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setIsDragging(true);
        } else if (e.type === 'dragleave') {
            setIsDragging(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file || !token) return;

        // Validate vault inputs if saving to vault
        if (saveToVault && (!keyLabel || !vaultPassword)) {
            setError('Please enter key label and vault password to save key securely');
            return;
        }

        setUploading(true);
        setError('');
        setUploadResult(null);

        try {
            // Step 1: Upload file (with vault password for digital signature)
            const result = await uploadFile(file, classification, token, vaultPassword);

            // Step 2: Save key to vault if option is checked
            if (saveToVault) {
                try {
                    await storeKeyInVault(
                        result.encryption_key,
                        vaultPassword,
                        '000000', // Dummy MFA for upload (not verified)
                        result.file_id,
                        keyLabel,
                        token
                    );
                    result.savedToVault = true;
                } catch (vaultError) {
                    // If vault storage fails, still show the key to user
                    result.vaultError = vaultError.message;
                }
            }

            // Manual mode (or vault save failed): hand the user a numbered key file
            if (!result.savedToVault) {
                const number = nextKeyNumber();
                const name = keyFileName(number);
                const text = buildKeyFile({
                    number, filename: file.name, fileId: result.file_id, keyHex: result.encryption_key
                });
                downloadTextFile(name, text);
                result.keyFile = { name, text };
            }

            setUploadResult(result);
            setFile(null); // Reset file after successful upload
            setVaultPassword('');
            setKeyLabel('');
        } catch (err) {
            setError(err.message || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="mb-8">
            <h3 className="text-xl mb-2 font-mono font-bold">START UPLOAD</h3>

            {/* Classification Selector */}
            <div className="mb-4 p-4 bg-white border-4 border-black">
                <label className="block font-mono font-bold mb-2">CLASSIFICATION LEVEL</label>
                <select
                    value={classification}
                    onChange={(e) => setClassification(e.target.value)}
                    className="w-full p-2 border-2 border-black font-mono"
                >
                    <option value="public">🟢 PUBLIC</option>
                    <option value="mission_logs">🟡 MISSION LOGS</option>
                    <option value="top_secret">🔴 TOP SECRET</option>
                </select>
            </div>

            {/* Save to Vault Option */}
            <div className="mb-4 p-4 bg-brutal-yellow border-4 border-black">
                <label className="flex items-center gap-3 cursor-pointer">
                    <input
                        type="checkbox"
                        checked={saveToVault}
                        onChange={(e) => setSaveToVault(e.target.checked)}
                        className="w-6 h-6 border-4 border-black"
                    />
                    <span className="font-mono font-bold">🔐 SAVE ENCRYPTION KEY TO VAULT</span>
                </label>
                <p className="text-xs font-mono mt-2 ml-9">
                    {saveToVault
                        ? 'Store key securely with password protection. No manual saving required!'
                        : 'Manual mode: a numbered key file (.txt) downloads automatically after upload. Keep it safe — you will select it to download this file.'}
                </p>
            </div>

            {/* Vault Inputs */}
            {saveToVault && (
                <div className="mb-4 p-4 bg-white border-4 border-black space-y-3">
                    <div>
                        <label className="block font-mono font-bold text-sm mb-1">KEY LABEL *</label>
                        <input
                            type="text"
                            value={keyLabel}
                            onChange={(e) => setKeyLabel(e.target.value)}
                            placeholder="e.g., Telemetry Report Jan 2026"
                            className="w-full p-2 border-2 border-black font-mono text-sm"
                            required={saveToVault}
                        />
                        <p className="text-xs text-gray-600 mt-1 font-mono">Give this key a memorable name</p>
                    </div>
                    <div>
                        <label className="block font-mono font-bold text-sm mb-1">VAULT PASSWORD *</label>
                        <input
                            type="password"
                            value={vaultPassword}
                            onChange={(e) => setVaultPassword(e.target.value)}
                            placeholder="Enter vault password"
                            className="w-full p-2 border-2 border-black font-mono text-sm"
                            required={saveToVault}
                        />
                        <p className="text-xs text-gray-600 mt-1 font-mono">MFA required only when retrieving</p>
                    </div>
                </div>
            )}

            <div
                className={`
                    border-4 border-black border-dashed p-10 text-center cursor-pointer transition-all
                    ${isDragging ? 'bg-yellow-200 scale-[1.02]' : 'bg-white hover:bg-gray-50'}
                `}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-input').click()}
            >
                <input
                    id="file-input"
                    type="file"
                    className="hidden"
                    onChange={handleChange}
                />

                {!file ? (
                    <div className="flex flex-col items-center">
                        <UploadCloud size={48} className="mb-4 stroke-2" />
                        <p className="font-mono font-bold text-lg">DRAG SECURE DOCUMENTS HERE</p>
                        <p className="text-sm mt-2 bg-black text-white px-2">AES-256 AUTOMATIC ENCRYPTION</p>
                    </div>
                ) : (
                    <div className="text-left font-mono">
                        <p className="font-bold">📄 {file.name}</p>
                        <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>

                        <Button
                            onClick={handleUpload}
                            disabled={uploading}
                            className="mt-4 w-full bg-brutal-pink text-white hover:bg-pink-600"
                        >
                            {uploading ? 'ENCRYPTING & UPLOADING...' : 'UPLOAD FILE'}
                        </Button>
                    </div>
                )}
            </div>

            {error && (
                <div className="mt-4 bg-red-100 border-4 border-red-600 p-4 font-mono text-sm">
                    ❌ {error}
                </div>
            )}

            {uploadResult && (
                <div className="mt-4 bg-green-100 border-4 border-green-600 p-4 font-mono text-sm">
                    <p className="font-bold">✅ UPLOAD SUCCESS</p>
                    <p className="text-xs mt-2">File ID: {uploadResult.file_id}</p>
                    <p className="text-xs">Chunks: {uploadResult.total_chunks}</p>

                    {uploadResult.savedToVault ? (
                        <div className="mt-3 p-2 bg-brutal-blue text-white border-2 border-black">
                            <p className="font-bold text-xs">🔐 KEY SAVED TO VAULT SECURELY!</p>
                            <p className="text-xs mt-1">You can retrieve it anytime with your vault password + MFA</p>
                        </div>
                    ) : (
                        <div className="mt-3 p-2 bg-yellow-50 border-2 border-yellow-600">
                            {uploadResult.vaultError && (
                                <p className="font-bold text-xs mb-1">⚠️ Vault save failed: {uploadResult.vaultError}</p>
                            )}
                            <p className="font-bold text-xs mb-1">
                                🔑 KEY FILE DOWNLOADED: {uploadResult.keyFile?.name}
                            </p>
                            <p className="text-xs">
                                Keep it safe. To download this file later, click DL and select this key file.
                            </p>
                            <button
                                type="button"
                                onClick={() => downloadTextFile(uploadResult.keyFile.name, uploadResult.keyFile.text)}
                                className="mt-2 text-xs font-bold underline"
                            >
                                Didn't download? Save the key file again
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
