import React from 'react';
import { FileList } from './FileList';
import { FileText } from 'lucide-react';

export const FilesPage = ({ token }) => {
    return (
        <div className="min-h-screen bg-brutal-bg p-8">
            <div className="max-w-7xl mx-auto">
                {/* Page Header */}
                <div className="mb-8 border-b-4 border-black pb-4">
                    <div className="flex items-center gap-4 mb-2">
                        <FileText size={48} className="stroke-[3px]" />
                        <h1 className="text-5xl font-black">FILE ARCHIVE</h1>
                    </div>
                    <p className="font-mono text-lg ml-16">
                        Browse and download encrypted files
                    </p>
                </div>

                {/* FileList Component */}
                <FileList token={token} />

                {/* Info Section */}
                <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white border-4 border-black p-4">
                        <h4 className="font-mono font-bold mb-2">🔒 ENCRYPTED</h4>
                        <p className="text-sm font-mono">All files are encrypted at rest with AES-256</p>
                    </div>
                    <div className="bg-white border-4 border-black p-4">
                        <h4 className="font-mono font-bold mb-2">🗝️ KEY REQUIRED</h4>
                        <p className="text-sm font-mono">Provide encryption key or retrieve from vault</p>
                    </div>
                    <div className="bg-white border-4 border-black p-4">
                        <h4 className="font-mono font-bold mb-2">📊 CLASSIFIED</h4>
                        <p className="text-sm font-mono">Files organized by security classification</p>
                    </div>
                </div>
            </div>
        </div>
    );
};
