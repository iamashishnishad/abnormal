import React, { useState, useEffect } from 'react';
import FileUpload from './components/FileUpload';
import SearchAndFilter from './components/SearchAndFilter';
import StorageStats from './components/StorageStats';
import { fileService } from './services/fileService';
import { File, SearchParams } from './types/file';
import './App.css';
import { DocumentIcon, TrashIcon, ArrowDownTrayIcon, DocumentDuplicateIcon } from '@heroicons/react/24/outline';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function App() {
    const queryClient = useQueryClient();
    const [files, setFiles] = useState<File[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [fileToDelete, setFileToDelete] = useState<File | null>(null);
    const [deleteError, setDeleteError] = useState<string | null>(null);

    const fetchFiles = async (params?: SearchParams) => {
        try {
            setLoading(true);
            const data = await fileService.searchFiles(params || {});
            setFiles(data);
        } catch (err) {
            setError('Failed to load files');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFiles();
    }, []);

    const handleUploadSuccess = (file: File) => {
        setFiles(prev => [file, ...prev]);
        queryClient.invalidateQueries({ queryKey: ['storageStats'] });
    };

    const handleSearch = (params: SearchParams) => {
        fetchFiles(params);
    };

    // Mutation for deleting files
    const deleteMutation = useMutation({
        mutationFn: fileService.deleteFile,
        onSuccess: () => {
            // Remove the deleted file from the local state
            setFiles(prev => prev.filter(f => f.id !== fileToDelete?.id));
            setFileToDelete(null);
            setDeleteError(null);
            // Refresh the file list and storage stats
            queryClient.invalidateQueries({ queryKey: ['storageStats'] });
            fetchFiles();
        },
        onError: (error: Error) => {
            setDeleteError(error.message || 'Failed to delete file');
        },
    });

    // Mutation for downloading files
    const downloadMutation = useMutation({
        mutationFn: ({ fileUrl, filename }: { fileUrl: string; filename: string }) =>
            fileService.downloadFile(fileUrl, filename),
    });

    const handleDelete = async (file: File) => {
        setFileToDelete(file);
    };

    const confirmDelete = async () => {
        if (fileToDelete) {
            try {
                await deleteMutation.mutateAsync(fileToDelete.id);
            } catch (err) {
                console.error('Delete error:', err);
            }
        }
    };

    const handleDownload = async (fileUrl: string, filename: string) => {
        try {
            await downloadMutation.mutateAsync({ fileUrl, filename });
        } catch (err) {
            console.error('Download error:', err);
        }
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>File Hub</h1>
            </header>

            <main className="App-main">
                <div className="upload-section">
                    <FileUpload
                        onUploadSuccess={handleUploadSuccess}
                        onUploadError={setError}
                    />
                </div>

                <div className="stats-section">
                    <StorageStats />
                </div>

                <div className="search-section">
                    <SearchAndFilter onSearch={handleSearch} />
                </div>

                <div className="files-section">
                    {loading ? (
                        <div>Loading files...</div>
                    ) : error ? (
                        <div className="error">{error}</div>
                    ) : (
                        <div className="files-grid">
                            {files.map(file => (
                                <div key={file.id} className="file-card">
                                    <div className="mb-2">
                                        <h3 className="text-lg font-medium text-gray-900 truncate">{file.original_filename}</h3>
                                    </div>
                                    <div className="space-y-2">
                                        <p className="text-sm text-gray-500">Type: {file.file_type}</p>
                                        <p className="text-sm text-gray-500">Size: {file.size_human}</p>
                                        <p className="text-sm text-gray-500">Uploaded: {new Date(file.uploaded_at).toLocaleDateString()}</p>
                                        {file.is_duplicate && (
                                            <p className="text-sm text-yellow-600">
                                                Duplicate of: {file.original_file_name}
                                            </p>
                                        )}
                                    </div>
                                    <div className="mt-4 pt-4 border-t border-gray-200">
                                        <div className="flex space-x-2">
                                            <button
                                                onClick={() => handleDownload(file.file, file.original_filename)}
                                                disabled={downloadMutation.isPending}
                                                className="flex-1 flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                                            >
                                                <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                                                Download
                                            </button>
                                            <button
                                                onClick={() => handleDelete(file)}
                                                disabled={deleteMutation.isPending}
                                                className="flex-1 flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                                            >
                                                <TrashIcon className="h-4 w-4 mr-2" />
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>

            {/* Delete Confirmation Modal */}
            {fileToDelete && (
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">Delete File</h3>
                        <p className="text-sm text-gray-500 mb-6">
                            Are you sure you want to delete "{fileToDelete.original_filename}"? This action cannot be undone.
                        </p>
                        {deleteError && (
                            <div className="mb-4 text-sm text-red-600 bg-red-50 p-2 rounded">
                                {deleteError}
                            </div>
                        )}
                        <div className="flex justify-end space-x-3">
                            <button
                                onClick={() => {
                                    setFileToDelete(null);
                                    setDeleteError(null);
                                }}
                                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmDelete}
                                disabled={deleteMutation.isPending}
                                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                            >
                                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;
