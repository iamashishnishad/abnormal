import axios from 'axios';
import { File, StorageStats, SearchParams } from '../types/file';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

interface DuplicateCheckResponse {
  is_duplicate: boolean;
  original_file_name?: string;
  original_file_id?: string;
}

export const fileService = {
  // Get all files with optional filters
  getFiles: async (params?: SearchParams): Promise<File[]> => {
    const response = await axios.get(`${API_URL}/files/`, { params });
    return response.data;
  },

  // Check if a file is a duplicate
  checkDuplicate: async (file: Blob): Promise<DuplicateCheckResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_URL}/files/check_duplicate/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Upload a file
  uploadFile: async (file: Blob): Promise<File> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_URL}/files/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Delete a file
  deleteFile: async (id: string): Promise<void> => {
    await axios.delete(`${API_URL}/files/${id}/`);
  },

  // Search files with advanced filters
  searchFiles: async (params: SearchParams): Promise<File[]> => {
    const response = await axios.get(`${API_URL}/files/search/`, { params });
    return response.data;
  },

  // Get storage statistics
  getStorageStats: async (): Promise<StorageStats> => {
    const response = await axios.get(`${API_URL}/files/storage_stats/`);
    return response.data;
  },

  async downloadFile(fileUrl: string, filename: string): Promise<void> {
    try {
      const response = await axios.get(fileUrl, {
        responseType: 'blob',
      });
      
      // Create a blob URL and trigger download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw new Error('Failed to download file');
    }
  },
}; 