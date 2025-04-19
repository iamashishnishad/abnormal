export interface File {
  id: string;
  file: string;
  original_filename: string;
  description?: string;
  size: number;
  file_hash: string;
  uploaded_at: string;
  is_duplicate: boolean;
  original_file?: string;
  file_type: string;
} 