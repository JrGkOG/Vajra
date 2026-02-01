import React, { useState } from 'react';
import { UploadCloud } from 'lucide-react';
import { uploadFile } from '../../services/api';
import { Button } from '../../components/ui/Button';

export const Upload = ({ token }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [file, setFile] = useState(null);
    const [classification, setClassification] = useState('public');
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);
    const [error, setError] = useState('');

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

        setUploading(true);
        setError('');
        setUploadResult(null);

        try {
            const result = await uploadFile(file, classification, token);
            setUploadResult(result);
            setFile(null); // Reset file after successful upload
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
                    <div className="mt-3 p-2 bg-yellow-50 border-2 border-yellow-600">
                        <p className="font-bold text-xs mb-1">🔑 ENCRYPTION KEY (SAVE THIS!):</p>
                        <p className="break-all text-xs">{uploadResult.encryption_key}</p>
                    </div>
                </div>
            )}
        </div>
    );
};
