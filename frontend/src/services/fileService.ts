// import axios from 'axios';
// import { File, StorageStats, SearchParams } from '../types/file';

// const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// interface DuplicateCheckResponse {
//   is_duplicate: boolean;
//   original_file_name?: string;
//   original_file_id?: string;
// }

// export const fileService = {
//   // Get all files with optional filters
//   getFiles: async (params?: SearchParams): Promise<File[]> => {
//     const response = await axios.get(`${API_URL}/files/`, { params });
//     return response.data;
//   },

//   // Check if a file is a duplicate
//   checkDuplicate: async (file: Blob): Promise<DuplicateCheckResponse> => {
//     const formData = new FormData();
//     formData.append('file', file);
//     const response = await axios.post(`${API_URL}/files/check_duplicate/`, formData, {
//       headers: {
//         'Content-Type': 'multipart/form-data',
//       },
//     });
//     return response.data;
//   },

//   // Upload a file
//   uploadFile: async (file: Blob): Promise<File> => {
//     const formData = new FormData();
//     formData.append('file', file);
//     const response = await axios.post(`${API_URL}/files/`, formData, {
//       headers: {
//         'Content-Type': 'multipart/form-data',
//       },
//     });
//     return response.data;
//   },

//   // Delete a file
//   deleteFile: async (id: string): Promise<void> => {
//     await axios.delete(`${API_URL}/files/${id}/`);
//   },

//   // Search files with advanced filters
//   searchFiles: async (params: SearchParams): Promise<File[]> => {
//     const response = await axios.get(`${API_URL}/files/search/`, { params });
//     return response.data;
//   },

//   // Get storage statistics
//   getStorageStats: async (): Promise<StorageStats> => {
//     const response = await axios.get(`${API_URL}/files/storage_stats/`);
//     return response.data;
//   },

//   async downloadFile(fileUrl: string, filename: string): Promise<void> {
//     try {
//       const response = await axios.get(fileUrl, {
//         responseType: 'blob',
//       });
      
//       // Create a blob URL and trigger download
//       const blob = new Blob([response.data]);
//       const url = window.URL.createObjectURL(blob);
//       const link = document.createElement('a');
//       link.href = url;
//       link.download = filename;
//       document.body.appendChild(link);
//       link.click();
//       document.body.removeChild(link);
//       window.URL.revokeObjectURL(url);
//     } catch (error) {
//       console.error('Download error:', error);
//       throw new Error('Failed to download file');
//     }
//   },
// }; 



import axios from 'axios';
import { File, StorageStats, SearchParams } from '../types/file';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

interface DuplicateCheckResponse {
  is_duplicate: boolean;
  file_hash: string;
  original_file_name?: string;
  original_file_id?: string;
}

// Helper function to calculate SHA-256 hash of a file
async function calculateFileHash(file: Blob): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

export const fileService = {
  // Get all files with optional filters
  getFiles: async (params?: SearchParams): Promise<File[]> => {
    const response = await axios.get(`${API_URL}/files/`, { params });
    return response.data;
  },

  // Check if a file is a duplicate
  checkDuplicate: async (file: Blob): Promise<DuplicateCheckResponse> => {
    const fileHash = await calculateFileHash(file);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post(`${API_URL}/files/check_duplicate/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return {
        is_duplicate: response.data.is_duplicate,
        file_hash: fileHash,
        ...(response.data.original_file_name && { original_file_name: response.data.original_file_name }),
        ...(response.data.original_file_id && { original_file_id: response.data.original_file_id }),
      };
    } catch (error) {
      console.error('Error checking duplicate:', error);
      throw new Error('Failed to check duplicate');
    }
  },

  // Upload a file
  uploadFile: async (file: Blob): Promise<File> => {
    // Check for duplicate first
    const duplicateCheck = await fileService.checkDuplicate(file);
    
    const metadata = {
      is_duplicate: duplicateCheck.is_duplicate,
      file_hash: duplicateCheck.file_hash,
      ...(duplicateCheck.is_duplicate && {
        original_file_name: duplicateCheck.original_file_name,
        original_file_id: duplicateCheck.original_file_id,
      }),
    };

    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    try {
      const response = await axios.post(`${API_URL}/files/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading file:', error);
      throw new Error('Failed to upload file');
    }
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