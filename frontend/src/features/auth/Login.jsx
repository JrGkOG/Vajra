import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { login as apiLogin } from '../../services/api';

export const Login = ({ onLogin }) => {
    const [step, setStep] = useState('login'); // login | mfa
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [mfaCode, setMfaCode] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await apiLogin(username, password);
            console.log("✅ Login successful:", response);

            // For this PoC, we'll simulate MFA step
            setStep('mfa');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleMfaVerify = async (e) => {
        e.preventDefault();

        // Simulate MFA verification (in real app, call backend)
        try {
            const response = await apiLogin(username, password);
            onLogin({
                user: response.user,
                token: response.access_token
            });
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-brutal-bg p-4">
            <div className="max-w-md w-full">
                <div className="mb-8 text-center">
                    <h1 className="text-5xl font-black mb-2 stroke-black">VAJRA</h1>
                    <p className="font-mono text-sm bg-black text-white inline-block px-2 py-1">SECURE FILE TRANSFER SYSTEM</p>
                </div>

                <Card title={step === 'login' ? 'IDENTIFY YOURSELF' : 'SECURITY CHECK'}>
                    {error && (
                        <div className="bg-red-100 border-4 border-red-600 p-3 mb-4 font-mono text-sm text-red-800">
                            ⚠️ ERROR: {error}
                        </div>
                    )}

                    {step === 'login' ? (
                        <form onSubmit={handleLogin} className="space-y-4">
                            <div>
                                <label className="block font-mono font-bold mb-1">USERNAME</label>
                                <Input
                                    placeholder="commander"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block font-mono font-bold mb-1">PASSWORD</label>
                                <Input
                                    type="password"
                                    placeholder="••••••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                            </div>
                            <Button type="submit" className="w-full mt-4" disabled={loading}>
                                {loading ? 'AUTHENTICATING...' : 'INITIATE SESSION'}
                            </Button>
                        </form>
                    ) : (
                        <form onSubmit={handleMfaVerify} className="space-y-4">
                            <div className="bg-yellow-100 border-l-4 border-black p-4 mb-4 font-mono text-sm">
                                ⚠️ MFA REQ: Enter code from authenticator.
                            </div>
                            <div>
                                <label className="block font-mono font-bold mb-1">MFA CODE</label>
                                <Input
                                    placeholder="000 000"
                                    className="text-center tracking-widest text-xl"
                                    value={mfaCode}
                                    onChange={(e) => setMfaCode(e.target.value)}
                                />
                            </div>
                            <Button type="submit" className="w-full mt-4 bg-brutal-pink text-white hover:bg-pink-600">
                                VERIFY IDENTITY
                            </Button>
                        </form>
                    )}
                </Card>
            </div>
        </div>
    );
};
