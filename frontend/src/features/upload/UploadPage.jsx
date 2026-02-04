import React from 'react';
import { Upload } from '../files/Upload';
import { UploadCloud } from 'lucide-react';

export const UploadPage = ({ token }) => {
    return (
        <div className="min-h-screen bg-brutal-bg p-8">
            <div className="max-w-4xl mx-auto">
                {/* Page Header */}
                <div className="mb-8 border-b-4 border-black pb-4">
                    <div className="flex items-center gap-4 mb-2">
                        <UploadCloud size={48} className="stroke-[3px]" />
                        <h1 className="text-5xl font-black">SECURE UPLOAD</h1>
                    </div>
                    <p className="font-mono text-lg ml-16">
                        Upload and encrypt files with AES-256-GCM encryption
                    </p>
                </div>

                {/* Upload Component */}
                <Upload token={token} />

                {/* Info Section */}
                <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white border-4 border-black p-4">
                        <h4 className="font-mono font-bold mb-2">🔐 ENCRYPTION</h4>
                        <p className="text-sm font-mono">Files are encrypted with AES-256-GCM before storage</p>
                    </div>
                    <div className="bg-white border-4 border-black p-4">
                        <h4 className="font-mono font-bold mb-2">🗝️ KEY VAULT</h4>
                        <p className="text-sm font-mono">Store encryption keys securely with password protection</p>
                    </div>
                    <div className="bg-white border-4 border-black p-4">
                        <h4 className="font-mono font-bold mb-2">📊 CLASSIFICATION</h4>
                        <p className="text-sm font-mono">Choose security level: Public, Mission Logs, or Top Secret</p>
                    </div>
                </div>
            </div>
        </div>
    );
};
