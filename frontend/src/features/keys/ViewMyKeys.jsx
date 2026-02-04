import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, Copy, Key, Shield, QrCode } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { getMySignatureKeys } from '../../services/api';
import QRCodeLib from 'qrcode';

export const ViewMyKeys = ({ token }) => {
    const [keys, setKeys] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showPublicKey, setShowPublicKey] = useState(false);
    const [showQRCode, setShowQRCode] = useState(false);
    const [qrCodeDataURL, setQrCodeDataURL] = useState('');
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        fetchKeys();
    }, [token]);

    const fetchKeys = async () => {
        setLoading(true);
        try {
            const result = await getMySignatureKeys(token);
            setKeys(result);
        } catch (err) {
            console.error('Failed to fetch keys:', err);
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const generateQRCode = async () => {
        if (!keys?.public_key) return;
        try {
            const dataURL = await QRCodeLib.toDataURL(keys.public_key, {
                width: 300,
                margin: 2,
                color: {
                    dark: '#000000',
                    light: '#FFFFFF'
                }
            });
            setQrCodeDataURL(dataURL);
            setShowQRCode(true);
        } catch (err) {
            console.error('Failed to generate QR code:', err);
        }
    };

    if (loading) {
        return (
            <div className="text-center p-12 font-mono">
                <div className="inline-block animate-spin mb-4">⚙️</div>
                <p>LOADING KEYS...</p>
            </div>
        );
    }

    if (!keys || !keys.has_keys) {
        return (
            <div className="bg-white border-4 border-black shadow-hard p-8 text-center font-mono">
                <Key size={48} className="mx-auto mb-4 text-gray-400" />
                <h3 className="text-xl font-bold mb-2">NO SIGNATURE KEYS</h3>
                <p className="text-sm text-gray-600">
                    You haven't generated signature keys yet.
                </p>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-mono font-bold mb-6 border-b-4 border-black pb-2">
                🔐 MY SIGNATURE KEYS
            </h2>

            {/* Key Information */}
            <div className="bg-white border-4 border-black shadow-hard p-6 mb-6">
                <div className="grid grid-cols-2 gap-4 text-sm font-mono mb-6">
                    <div>
                        <div className="text-gray-600">Algorithm</div>
                        <div className="font-bold">{keys.algorithm.toUpperCase()}</div>
                    </div>
                    <div>
                        <div className="text-gray-600">Storage Method</div>
                        <div className="font-bold">
                            {keys.storage_method === 'password' ? '🔒 PASSWORD' : '📁 CLIENT FILE'}
                        </div>
                    </div>
                    <div>
                        <div className="text-gray-600">Private Key Stored</div>
                        <div className="font-bold">
                            {keys.has_private_key ? '✅ YES (Encrypted)' : '❌ NO (You manage it)'}
                        </div>
                    </div>
                    <div>
                        <div className="text-gray-600">Generated At</div>
                        <div className="font-bold text-xs">
                            {keys.keys_generated_at ? new Date(keys.keys_generated_at).toLocaleString() : 'Unknown'}
                        </div>
                    </div>
                </div>

                {/* Public Key */}
                <div className="border-2 border-black p-4 mb-4">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="font-bold font-mono">PUBLIC KEY</h3>
                        <div className="flex gap-2">
                            <Button
                                onClick={() => setShowPublicKey(!showPublicKey)}
                                className="py-1 px-2 text-xs"
                            >
                                {showPublicKey ? <EyeOff size={14} /> : <Eye size={14} />}
                                {showPublicKey ? ' HIDE TEXT' : ' SHOW TEXT'}
                            </Button>
                            <Button
                                onClick={() => copyToClipboard(keys.public_key)}
                                className="py-1 px-2 text-xs bg-brutal-blue text-white"
                            >
                                <Copy size={14} />
                                {copied ? ' COPIED!' : ' COPY KEY'}
                            </Button>
                            <Button
                                onClick={() => {
                                    if (showQRCode) {
                                        setShowQRCode(false);
                                    } else {
                                        generateQRCode();
                                    }
                                }}
                                className="py-1 px-2 text-xs bg-brutal-purple text-white"
                            >
                                <QrCode size={14} />
                                {showQRCode ? ' HIDE QR' : ' SHOW QR'}
                            </Button>
                        </div>
                    </div>

                    {/* Text Display */}
                    {showPublicKey && (
                        <div className="bg-gray-50 p-3 border border-gray-300 font-mono text-xs break-all mb-3">
                            {keys.public_key}
                        </div>
                    )}

                    {/* QR Code Display */}
                    {showQRCode && qrCodeDataURL && (
                        <div className="bg-white p-4 border border-gray-300 text-center">
                            <img
                                src={qrCodeDataURL}
                                alt="Public Key QR Code"
                                className="mx-auto mb-2"
                                style={{ width: '300px', height: '300px' }}
                            />
                            <p className="text-xs text-gray-600 font-mono">Scan this QR code to get the public key</p>
                        </div>
                    )}

                    {!showPublicKey && !showQRCode && (
                        <div className="bg-gray-100 p-3 text-center text-gray-500 text-sm font-mono">
                            Click "SHOW TEXT" to view the public key or "SHOW QR" to display as QR code
                        </div>
                    )}
                </div>

                {/* Private Key Status */}
                <div className="border-2 border-black p-4 bg-yellow-50">
                    <div className="flex items-start gap-3">
                        <Shield className="text-yellow-600 flex-shrink-0" size={24} />
                        <div className="text-sm font-mono">
                            <div className="font-bold mb-2">PRIVATE KEY</div>
                            {keys.storage_method === 'password' ? (
                                <div>
                                    <div className="mb-2">
                                        ✅ Your private key is encrypted and stored securely on the server.
                                    </div>
                                    <div className="text-xs text-gray-700">
                                        • Encrypted with your vault password using AES-256-GCM<br />
                                        • PBKDF2 with 100,000 iterations<br />
                                        • Cannot be decrypted without your vault password<br />
                                        • Not shown here for security reasons
                                    </div>
                                </div>
                            ) : (
                                <div>
                                    <div className="mb-2">
                                        📁 Your private key is NOT stored on the server.
                                    </div>
                                    <div className="text-xs text-gray-700">
                                        • You downloaded your private key file during key generation<br />
                                        • Keep it safe - you need it to sign files<br />
                                        • If lost, you'll need to generate new keys<br />
                                        • Server only has your public key for verification
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Security Notice */}
            <div className="bg-red-50 border-4 border-red-600 p-4 font-mono text-sm">
                <div className="font-bold mb-2">⚠️ SECURITY WARNINGS</div>
                <ul className="list-disc ml-4 space-y-1 text-xs">
                    <li>Never share your private key with anyone</li>
                    <li>Your public key can be safely shared - it's used to verify your signatures</li>
                    <li>If you suspect your private key is compromised, generate new keys immediately</li>
                    <li>Files signed with old keys will remain valid, but use new keys for future uploads</li>
                </ul>
            </div>
        </div>
    );
};
