export interface File {
  id: string;
  file: string;
  original_filename: string;
  file_type: string;
  size: number;
  uploaded_at: string;
  file_hash: string;
  is_duplicate: boolean;
  original_file: string | null;
  storage_saved: number;
  original_file_name?: string;
  storage_saved_human?: string;
  size_human?: string;
}

export interface StorageStats {
  total_files: number;
  total_size: number;
  total_storage_saved: number;
  duplicate_count: number;
  storage_efficiency: string;
}

export interface SearchParams {
  q?: string;
  file_type?: string;
  min_size?: number;
  max_size?: number;
  start_date?: string;
  end_date?: string;
} 