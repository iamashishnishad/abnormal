import React, { useState } from 'react';
import { SearchParams } from '../types/file';

interface SearchAndFilterProps {
    onSearch: (params: SearchParams) => void;
}

const SearchAndFilter: React.FC<SearchAndFilterProps> = ({ onSearch }) => {
    const [searchParams, setSearchParams] = useState<SearchParams>({});

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setSearchParams(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch(searchParams);
    };

    return (
        <form onSubmit={handleSubmit} className="search-filter-form">
            <div className="search-box">
                <input
                    type="text"
                    name="q"
                    placeholder="Search by filename..."
                    value={searchParams.q || ''}
                    onChange={handleInputChange}
                />
            </div>

            <div className="filters">
                <div className="filter-group">
                    <label>File Type:</label>
                    <input
                        type="text"
                        name="file_type"
                        placeholder="e.g., pdf, jpg"
                        value={searchParams.file_type || ''}
                        onChange={handleInputChange}
                    />
                </div>

                <div className="filter-group">
                    <label>Size Range:</label>
                    <div className="size-range">
                        <input
                            type="number"
                            name="min_size"
                            placeholder="Min size (bytes)"
                            value={searchParams.min_size || ''}
                            onChange={handleInputChange}
                        />
                        <span>to</span>
                        <input
                            type="number"
                            name="max_size"
                            placeholder="Max size (bytes)"
                            value={searchParams.max_size || ''}
                            onChange={handleInputChange}
                        />
                    </div>
                </div>

                <div className="filter-group">
                    <label>Date Range:</label>
                    <div className="date-range">
                        <input
                            type="date"
                            name="start_date"
                            value={searchParams.start_date || ''}
                            onChange={handleInputChange}
                        />
                        <span>to</span>
                        <input
                            type="date"
                            name="end_date"
                            value={searchParams.end_date || ''}
                            onChange={handleInputChange}
                        />
                    </div>
                </div>
            </div>

            <button type="submit" className="search-button">
                Search
            </button>
        </form>
    );
};

export default SearchAndFilter; 