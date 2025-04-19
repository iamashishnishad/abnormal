import React from 'react';
import { fileService } from '../services/fileService';
import { StorageStats as StorageStatsType } from '../types/file';
import { useQuery } from '@tanstack/react-query';

const StorageStats: React.FC = () => {
    const { data: stats, isLoading, error } = useQuery<StorageStatsType>({
        queryKey: ['storageStats'],
        queryFn: fileService.getStorageStats,
        refetchInterval: 5000, // Refetch every 5 seconds
    });

    if (isLoading) return <div>Loading statistics...</div>;
    if (error) return <div className="error">Failed to load storage statistics</div>;
    if (!stats) return null;

    return (
        <div className="storage-stats">
            <h2>Storage Statistics</h2>
            <div className="stats-grid">
                <div className="stat-item">
                    <h3>Total Files</h3>
                    <p>{stats.total_files}</p>
                </div>
                <div className="stat-item">
                    <h3>Total Size</h3>
                    <p>{stats.total_size} bytes</p>
                </div>
                <div className="stat-item">
                    <h3>Storage Saved</h3>
                    <p>{stats.total_storage_saved} bytes</p>
                </div>
                <div className="stat-item">
                    <h3>Duplicate Files</h3>
                    <p>{stats.duplicate_count}</p>
                </div>
                <div className="stat-item">
                    <h3>Storage Efficiency</h3>
                    <p>{stats.storage_efficiency}</p>
                </div>
            </div>
        </div>
    );
};

export default StorageStats; 