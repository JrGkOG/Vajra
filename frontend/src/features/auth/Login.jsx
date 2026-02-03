import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Shield, Lock, Mail } from 'lucide-react';
import { Footer } from '../../components/Footer';
import { loginPassword, loginMFA } from '../../services/api';

export const Login = ({ onLogin }) => {
    const [step, setStep] = useState('login'); // login | mfa
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [mfaCode, setMfaCode] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setSuccessMessage('');
        setLoading(true);

        try {
            // Step 1: Send email + password, backend sends MFA code
            const response = await loginPassword(email, password);
            console.log("✅ Password verified, MFA code sent to email");

            setSuccessMessage(response.message);
            setStep('mfa'); // Move to MFA verification step
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleMfaVerify = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            // Step 2: Verify MFA code
            const response = await loginMFA(email, mfaCode);
            console.log("✅ MFA verified, logging in:", response);

            onLogin({
                user: response.user,
                token: response.access_token
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-brutal-bg flex flex-col p-6">
            {/* Main Content */}
            <div className="flex-1 flex items-center justify-center">
                <div className="max-w-2xl w-full">
                    {/* Header */}
                    <div className="text-center mb-12">
                        <Link to="/" className="inline-block mb-8 p-8 bg-brutal-yellow border-8 border-black shadow-hard-xl hover:shadow-hard-lg hover:-translate-y-1 transition-all">
                            <h1 className="text-7xl font-black tracking-tighter">VAJRA</h1>
                        </Link>
                        <p className="text-2xl font-mono font-black uppercase mb-2">
                            Satellite Telemetry Exchange
                        </p>
                        <p className="text-lg font-bold mb-6">SECURE ACCESS TERMINAL</p>
                    </div>

                    {/* Login Card */}
                    <div className="bg-white border-8 border-black shadow-hard-xl p-10">
                        {/* Card Header */}
                        <div className="mb-8 flex items-center gap-4">
                            {step === 'login' ? (
                                <>
                                    <Shield size={40} className="stroke-[3px]" />
                                    <h2 className="text-3xl font-black">IDENTIFY YOURSELF</h2>
                                </>
                            ) : (
                                <>
                                    <Lock size={40} className="stroke-[3px]" />
                                    <h2 className="text-3xl font-black">SECURITY CHECK</h2>
                                </>
                            )}
                        </div>

                        {/* Error Display */}
                        {error && (
                            <div className="bg-brutal-pink text-white border-6 border-black p-4 mb-6 font-mono shadow-hard-sm">
                                <p className="font-bold">⚠️ ERROR: {error}</p>
                            </div>
                        )}

                        {/* Success Message */}
                        {successMessage && (
                            <div className="bg-brutal-green text-white border-6 border-black p-4 mb-6 font-mono shadow-hard-sm">
                                <p className="font-bold">✅ {successMessage}</p>
                            </div>
                        )}

                        {/* Login Form */}
                        {step === 'login' ? (
                            <form onSubmit={handleLogin} className="space-y-6">
                                <div>
                                    <label className="block font-mono font-bold text-lg mb-2">EMAIL</label>
                                    <input
                                        type="email"
                                        placeholder="admin@vajra.mil"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="w-full p-4 border-6 border-black shadow-hard-sm focus:outline-none focus:shadow-hard transition-all font-mono text-lg"
                                    />
                                </div>
                                <div>
                                    <label className="block font-mono font-bold text-lg mb-2">PASSWORD</label>
                                    <input
                                        type="password"
                                        placeholder="••••••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        className="w-full p-4 border-6 border-black shadow-hard-sm focus:outline-none focus:shadow-hard transition-all font-mono text-lg"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full brutal-btn bg-brutal-blue text-white text-xl py-4 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? 'SENDING MFA CODE...' : 'SEND MFA CODE'}
                                </button>
                            </form>
                        ) : (
                            <form onSubmit={handleMfaVerify} className="space-y-6">
                                <div className="bg-brutal-yellow border-6 border-black p-4 mb-6 font-mono shadow-hard-sm">
                                    <p className="font-bold text-center">📧 CHECK YOUR EMAIL</p>
                                    <p className="text-sm mt-2">{email}</p>
                                    <p className="text-sm mt-2">Enter the 6-digit code we sent you</p>
                                </div>
                                <div>
                                    <label className="block font-mono font-bold text-lg mb-2">MFA CODE</label>
                                    <input
                                        type="text"
                                        placeholder="000000"
                                        value={mfaCode}
                                        onChange={(e) => setMfaCode(e.target.value)}
                                        maxLength="6"
                                        required
                                        className="w-full p-4 border-6 border-black shadow-hard-sm focus:outline-none focus:shadow-hard transition-all font-mono text-xl text-center tracking-widest"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full brutal-btn bg-brutal-pink text-white text-xl py-4 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? 'VERIFYING...' : 'VERIFY & LOGIN'}
                                </button>
                            </form>
                        )}

                        {/* Back Link */}
                        <div className="mt-6 text-center">
                            <Link to="/" className="font-mono text-sm hover:underline">
                                ← Back to Home
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <Footer />
        </div>
    );
};
