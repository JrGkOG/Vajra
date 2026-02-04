import React, { useState } from 'react';
import { Key, Download, Upload, Shield } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { generateSignatureKeys, registerClientPublicKey } from '../../services/api';
import { generateEd25519KeyPair, downloadPrivateKey, readPrivateKeyFile } from '../../utils/cryptoKeys';

export const KeyManagement = ({ token }) => {
    const [method, setMethod] = useState(null); // 'password' or 'client_file'
    const [vaultPassword, setVaultPassword] = useState('');
    const [generating, setGenerating] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');

    const handlePasswordMethod = async () => {
        if (!vaultPassword) {
            setError('Please enter your vault password');
            return;
        }

        setGenerating(true);
        setError('');
        setResult(null);

        try {
            const response = await generateSignatureKeys(token, vaultPassword);
            setResult({
                ...response,
                message: '✅ Keys generated! Private key encrypted and stored securely.'
            });
            setVaultPassword('');
        } catch (err) {
            setError(err.message || 'Failed to generate keys');
        } finally {
            setGenerating(false);
        }
    };

    const handleClientFileMethod = async () => {
        setGenerating(true);
        setError('');
        setResult(null);

        try {
            // Generate keys in browser
            const { publicKey, privateKey } = await generateEd25519KeyPair();

            // Download private key file for user
            downloadPrivateKey(privateKey, 'vajra_signature_key.pem');

            // Register only public key on server
            const response = await registerClientPublicKey(token, publicKey);

            setResult({
                ...response,
                message: '✅ Keys generated! Private key downloaded. Keep it safe!'
            });
        } catch (err) {
            setError(err.message || 'Failed to generate keys');
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-6">
            <h2 className="text-2xl font-mono font-bold mb-6 border-b-4 border-black pb-2">
                🔐 SIGNATURE KEY MANAGEMENT
            </h2>

            {!method ? (
                <div className="grid md:grid-cols-2 gap-6">
                    {/* Password Method */}
                    <div className="bg-white border-4 border-black shadow-hard p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <Shield className="text-brutal-blue" size={32} />
                            <h3 className="font-mono font-bold text-lg">PASSWORD METHOD</h3>
                        </div>
                        <p className="text-sm mb-4 font-mono">
                            Private key encrypted with your vault password and stored on server.
                            Convenient - no key management needed.
                        </p>
                        <div className="space-y-2 text-xs mb-4">
                            <div className="flex items-start gap-2">
                                <span className="text-green-600">✓</span>
                                <span>Convenient - use vault password to sign</span>
                            </div>
                            <div className="flex items-start gap-2">
                                <span className="text-green-600">✓</span>
                                <span>AES-256-GCM + PBKDF2 (100k iterations)</span>
                            </div>
                            <div className="flex items-start gap-2">
                                <span className="text-yellow-600">⚠</span>
                                <span>Private key stored on server (encrypted)</span>
                            </div>
                        </div>
                        <Button
                            onClick={() => setMethod('password')}
                            className="w-full bg-brutal-blue text-white"
                        >
                            SELECT PASSWORD METHOD
                        </Button>
                    </div>

                    {/* Client File Method */}
                    <div className="bg-white border-4 border-black shadow-hard p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <Download className="text-brutal-yellow" size={32} />
                            <h3 className="font-mono font-bold text-lg">FILE METHOD</h3>
                        </div>
                        <p className="text-sm mb-4 font-mono">
                            Private key generated in browser and downloaded.
                            Maximum security - server never sees your private key.
                        </p>
                        <div className="space-y-2 text-xs mb-4">
                            <div className="flex items-start gap-2">
                                <span className="text-green-600">✓</span>
                                <span>Private key NEVER touches server</span>
                            </div>
                            <div className="flex items-start gap-2">
                                <span className="text-green-600">✓</span>
                                <span>Maximum security (like SSH keys)</span>
                            </div>
                            <div className="flex items-start gap-2">
                                <span className="text-red-600">❌</span>
                                <span>You must manage key file (if lost, can't sign)</span>
                            </div>
                        </div>
                        <Button
                            onClick={() => setMethod('client_file')}
                            className="w-full bg-brutal-yellow text-black"
                        >
                            SELECT FILE METHOD
                        </Button>
                    </div>
                </div>
            ) : (
                <div>
                    <button
                        onClick={() => {
                            setMethod(null);
                            setError('');
                            setResult(null);
                        }}
                        className="mb-4 text-sm font-mono underline"
                    >
                        ← Back to method selection
                    </button>

                    {method === 'password' && (
                        <div className="bg-white border-4 border-black shadow-hard p-6">
                            <h3 className="font-mono font-bold text-lg mb-4">
                                🔒 PASSWORD-BASED KEY GENERATION
                            </h3>
                            <p className="text-sm mb-4 font-mono">
                                Enter your vault password. Your private key will be encrypted and stored securely.
                            </p>

                            <div className="mb-4">
                                <label className="block font-mono font-bold text-sm mb-2">
                                    VAULT PASSWORD
                                </label>
                                <input
                                    type="password"
                                    value={vaultPassword}
                                    onChange={(e) => setVaultPassword(e.target.value)}
                                    placeholder="Enter vault password"
                                    className="w-full p-3 border-2 border-black font-mono"
                                />
                            </div>

                            <Button
                                onClick={handlePasswordMethod}
                                disabled={generating || !vaultPassword}
                                className="w-full bg-brutal-blue text-white"
                            >
                                {generating ? 'GENERATING...' : 'GENERATE & ENCRYPT KEYS'}
                            </Button>
                        </div>
                    )}

                    {method === 'client_file' && (
                        <div className="bg-white border-4 border-black shadow-hard p-6">
                            <h3 className="font-mono font-bold text-lg mb-4">
                                📥 FILE-BASED KEY GENERATION
                            </h3>
                            <p className="text-sm mb-4 font-mono">
                                Keys will be generated in your browser. Your private key will be downloaded automatically.
                            </p>

                            <div className="bg-yellow-50 border-2 border-yellow-500 p-4 mb-4 text-xs font-mono">
                                <strong>⚠️ IMPORTANT:</strong>
                                <ul className="list-disc ml-4 mt-2 space-y-1">
                                    <li>Save the downloaded key file in a secure location</li>
                                    <li>You'll need this file to sign uploads</li>
                                    <li>If you lose it, you can't sign new files</li>
                                    <li>Never share your private key file</li>
                                </ul>
                            </div>

                            <Button
                                onClick={handleClientFileMethod}
                                disabled={generating}
                                className="w-full bg-brutal-yellow text-black"
                            >
                                {generating ? 'GENERATING...' : 'GENERATE KEYS & DOWNLOAD'}
                            </Button>
                        </div>
                    )}
                </div>
            )}

            {/* Success Message */}
            {result && (
                <div className="mt-6 bg-green-100 border-4 border-green-600 p-6 font-mono">
                    <div className="font-bold mb-2">{result.message}</div>
                    <div className="text-sm space-y-1">
                        <div>Algorithm: {result.algorithm}</div>
                        <div>Storage Method: {result.storage_method}</div>
                    </div>
                </div>
            )}

            {/* Error Message */}
            {error && (
                <div className="mt-6 bg-red-100 border-4 border-red-600 p-4 font-mono text-sm">
                    ❌ {error}
                </div>
            )}
        </div>
    );
};
