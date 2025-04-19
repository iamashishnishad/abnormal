import React, { useState } from 'react';
import { fileService } from '../services/fileService';
import { CloudArrowUpIcon, DocumentDuplicateIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { File as FileType } from '../types/file';

interface FileUploadProps {
  onUploadSuccess: (file: FileType) => void;
  onUploadError: (error: string) => void;
  maxFileSize?: number; // in bytes
  onStorageSaved?: (savedBytes: number) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ 
  onUploadSuccess, 
  onUploadError,
  maxFileSize = 10 * 1024 * 1024, // Default 10MB
  onStorageSaved
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDuplicate, setIsDuplicate] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<{ originalFile: string; savedBytes: number } | null>(null);
  const queryClient = useQueryClient();
  const [isUploading, setIsUploading] = useState(false);

  const uploadMutation = useMutation<FileType, Error, File>({
    mutationFn: fileService.uploadFile,
    onSuccess: (file) => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      setSelectedFile(null);
      setError(null);
      setIsDuplicate(false);
      setDuplicateInfo(null);
      if (file.is_duplicate && onStorageSaved) {
        onStorageSaved(file.size);
      }
      onUploadSuccess(file);
    },
    onError: (error: Error) => {
      const errorMessage = error.message || 'Failed to upload file. Please try again.';
      setError(errorMessage);
      console.error('Upload error:', error);
      onUploadError(errorMessage);
    },
  });

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.size > maxFileSize) {
        const sizeInMB = (maxFileSize / (1024 * 1024)).toFixed(0);
        setError(`File size exceeds ${sizeInMB}MB limit`);
        return;
      }

      // Check for duplicates before uploading
      try {
        const duplicateCheck = await fileService.checkDuplicate(file);
        if (duplicateCheck.is_duplicate && duplicateCheck.original_file_name) {
          setIsDuplicate(true);
          setDuplicateInfo({
            originalFile: duplicateCheck.original_file_name,
            savedBytes: file.size
          });
          // Show a warning but allow upload
          setError('This file appears to be a duplicate. You can still upload it if needed.');
        } else {
          setIsDuplicate(false);
          setDuplicateInfo(null);
          setError(null);
        }
      } catch (err) {
        console.error('Duplicate check error:', err);
        setIsDuplicate(false);
        setDuplicateInfo(null);
        setError('Failed to check for duplicates. Please try again.');
      }

      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    setIsUploading(true);
    try {
      setError(null);
      const uploadedFile = await uploadMutation.mutateAsync(selectedFile);
      
      if (uploadedFile.is_duplicate) {
        // Show success message for duplicate upload
        setError('File uploaded successfully as a duplicate. Storage space saved!');
        if (onStorageSaved) {
          onStorageSaved(uploadedFile.storage_saved);
        }
      } else {
        setError('File uploaded successfully!');
      }
    } catch (err) {
      // Error handling is done in onError callback
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-6">
      <div className="flex items-center mb-4">
        <CloudArrowUpIcon className="h-6 w-6 text-primary-600 mr-2" />
        <h2 className="text-xl font-semibold text-gray-900">Upload File</h2>
      </div>
      <div className="mt-4 space-y-4">
        <div className="flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg">
          <div className="space-y-1 text-center">
            <div className="flex text-sm text-gray-600">
              <label
                htmlFor="file-upload"
                className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
              >
                <span>Upload a file</span>
                <input
                  id="file-upload"
                  name="file-upload"
                  type="file"
                  className="sr-only"
                  onChange={handleFileSelect}
                  disabled={isUploading}
                />
              </label>
              <p className="pl-1">or drag and drop</p>
            </div>
            <p className="text-xs text-gray-500">
              Any file up to {formatFileSize(maxFileSize)}
            </p>
          </div>
        </div>
        {selectedFile && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
              <div className="flex-1">
                <p className="font-medium">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">{formatFileSize(selectedFile.size)}</p>
              </div>
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setIsDuplicate(false);
                  setDuplicateInfo(null);
                  setError(null);
                }}
                className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none"
                title="Remove file"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
            {isDuplicate && duplicateInfo && (
              <div className="flex items-center text-sm text-yellow-600 bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                <DocumentDuplicateIcon className="h-5 w-5 mr-2 flex-shrink-0" />
                <div>
                  <p className="font-medium">Duplicate File Detected</p>
                  <p className="text-xs mt-1">Original file: {duplicateInfo.originalFile}</p>
                  <p className="text-xs mt-1 text-green-600">
                    Storage saved: {formatFileSize(duplicateInfo.savedBytes)}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
        {error && (
          <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
            {error}
          </div>
        )}
        <button
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
            !selectedFile || isUploading
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'
          }`}
        >
          {isUploading ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Uploading...
            </>
          ) : (
            'Upload'
          )}
        </button>
      </div>
    </div>
  );
};

export default FileUpload; 