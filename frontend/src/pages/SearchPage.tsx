import React, { useState } from 'react';
import { SearchResults } from '../components/SearchResults';
import { SearchParams } from '../types/file';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

export const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useState<SearchParams>({
    q: '',
    file_type: '',
    min_size: undefined,
    max_size: undefined,
    start_date: '',
    end_date: '',
  });

  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSearching(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setSearchParams(prev => {
      if (name === 'min_size' || name === 'max_size') {
        return {
          ...prev,
          [name]: value ? Number(value) : undefined
        };
      }
      return {
        ...prev,
        [name]: value
      };
    });
  };

  const handleSearchSubmit = () => {
    setIsSearching(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg p-6">
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <div>
                  <label htmlFor="q" className="block text-sm font-medium text-gray-700">
                    Search
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      name="q"
                      id="q"
                      value={searchParams.q}
                      onChange={handleInputChange}
                      className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md"
                      placeholder="Search files..."
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="file_type" className="block text-sm font-medium text-gray-700">
                    File Type
                  </label>
                  <select
                    id="file_type"
                    name="file_type"
                    value={searchParams.file_type}
                    onChange={handleInputChange}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                  >
                    <option value="">All Types</option>
                    <option value="image">Images</option>
                    <option value="document">Documents</option>
                    <option value="video">Videos</option>
                    <option value="audio">Audio</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="min_size" className="block text-sm font-medium text-gray-700">
                    Min Size (KB)
                  </label>
                  <input
                    type="number"
                    name="min_size"
                    id="min_size"
                    min="0"
                    value={searchParams.min_size || ''}
                    onChange={handleInputChange}
                    className="mt-1 focus:ring-primary-500 focus:border-primary-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label htmlFor="max_size" className="block text-sm font-medium text-gray-700">
                    Max Size (KB)
                  </label>
                  <input
                    type="number"
                    name="max_size"
                    id="max_size"
                    min="0"
                    value={searchParams.max_size || ''}
                    onChange={handleInputChange}
                    className="mt-1 focus:ring-primary-500 focus:border-primary-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">
                    Start Date
                  </label>
                  <input
                    type="date"
                    name="start_date"
                    id="start_date"
                    value={searchParams.start_date}
                    onChange={handleInputChange}
                    className="mt-1 focus:ring-primary-500 focus:border-primary-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
                    End Date
                  </label>
                  <input
                    type="date"
                    name="end_date"
                    id="end_date"
                    value={searchParams.end_date}
                    onChange={handleInputChange}
                    className="mt-1 focus:ring-primary-500 focus:border-primary-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setSearchParams({
                      q: '',
                      file_type: '',
                      min_size: undefined,
                      max_size: undefined,
                      start_date: '',
                      end_date: '',
                    });
                    setIsSearching(false);
                  }}
                  className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Clear
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Search
                </button>
              </div>
            </form>
          </div>

          <div className="mt-6">
            {isSearching && <SearchResults searchParams={searchParams} />}
          </div>
        </div>
      </div>
    </div>
  );
}; 