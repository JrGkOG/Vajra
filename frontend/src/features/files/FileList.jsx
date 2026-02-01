import React, { useEffect, useState } from 'react';
import { Download, Lock, RefreshCw } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { getFiles, downloadFile } from '../../services/api';

const ClassificationBadge = ({ level }) => {
    const styles = {
        top_secret: 'bg-red-500 text-white',
        mission_logs: 'bg-yellow-400 text-black',
        public: 'bg-green-400 text-black'
    };

    return (
        <span className={`border-2 border-black px-2 py-0.5 text-xs font-bold uppercase ${styles[level] || 'bg-gray-200'}`}>
            {level.replace('_', ' ')}
        </span>
    );
};

export const FileList = ({ token }) => {
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [downloadingId, setDownloadingId] = useState(null);

    const fetchFiles = async () => {
        if (!token) return;

        setLoading(true);
        setError('');

        try {
            const response = await getFiles(token);
            setFiles(response.files || []);
        } catch (err) {
            setError(err.message || 'Failed to fetch files');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFiles();
    }, [token]);

    const handleDownload = async (file) => {
        const encryptionKey = prompt('Enter encryption key (hex):');
        if (!encryptionKey) return;

        setDownloadingId(file.file_id);
        try {
            const blob = await downloadFile(file.file_id, encryptionKey, token);

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            alert(`Download failed: ${err.message}`);
        } finally {
            setDownloadingId(null);
        }
    };

    if (loading) {
        return (
            <div className="text-center p-12 font-mono">
                <RefreshCw className="animate-spin inline-block mb-4" size={32} />
                <p>LOADING SECURE VAULT...</p>
            </div>
        );
    }

    return (
        <div>
            <div className="flex justify-between items-end mb-4">
                <h3 className="text-xl font-mono font-bold">SECURE VAULT</h3>
                <div className="flex gap-2 items-center">
                    <span className="text-xs bg-black text-white px-2 py-1">TOTAL: {files.length} FILES</span>
                    <Button onClick={fetchFiles} className="text-xs py-1 px-2">
                        <RefreshCw size={14} className="inline mr-1" /> REFRESH
                    </Button>
                </div>
            </div>

            {error && (
                <div className="mb-4 bg-red-100 border-4 border-red-600 p-4 font-mono text-sm">
                    ❌ {error}
                </div>
            )}

            {files.length === 0 ? (
                <div className="bg-white border-4 border-black p-12 text-center font-mono">
                    <p className="text-lg font-bold">NO FILES IN VAULT</p>
                    <p className="text-sm mt-2">Upload a file to get started</p>
                </div>
            ) : (
                <div className="overflow-x-auto border-4 border-black shadow-hard">
                    <table className="w-full text-left font-mono">
                        <thead className="bg-brutal-bg border-b-4 border-black">
                            <tr>
                                <th className="p-4 border-r-4 border-black">FILENAME</th>
                                <th className="p-4 border-r-4 border-black">CLASS</th>
                                <th className="p-4 border-r-4 border-black">CHUNKS</th>
                                <th className="p-4 border-r-4 border-black">OWNER</th>
                                <th className="p-4">ACTION</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white">
                            {files.map((file, idx) => (
                                <tr key={file.file_id} className={idx !== files.length - 1 ? 'border-b-4 border-black' : ''}>
                                    <td className="p-4 border-r-4 border-black font-bold flex items-center gap-2">
                                        <Lock size={16} /> {file.filename}
                                    </td>
                                    <td className="p-4 border-r-4 border-black">
                                        <ClassificationBadge level={file.classification || 'public'} />
                                    </td>
                                    <td className="p-4 border-r-4 border-black text-sm">{file.total_chunks}</td>
                                    <td className="p-4 border-r-4 border-black text-sm">{file.owner_id}</td>
                                    <td className="p-4">
                                        <Button
                                            onClick={() => handleDownload(file)}
                                            disabled={downloadingId === file.file_id}
                                            className="py-1 px-3 text-sm flex items-center gap-2 bg-brutal-blue text-white hover:bg-blue-600"
                                        >
                                            <Download size={14} />
                                            {downloadingId === file.file_id ? 'DOWNLOADING...' : 'DOWNLOAD'}
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};
