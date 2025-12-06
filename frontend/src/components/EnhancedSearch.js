// frontend/src/components/EnhancedSearch.js
import React, { useState, useEffect } from 'react';
import { useMemory } from '../contexts/MemoryContext';

const EnhancedSearch = () => {
    const [query, setQuery] = useState('');
    const [memoryResults, setMemoryResults] = useState([]);
    const { searchMemories, trackActivity } = useMemory();

    useEffect(() => {
        // Arama aktivitesini takip et
        if (query.length > 2) {
            trackActivity('search', { query, timestamp: Date.now() });
        }
    }, [query, trackActivity]);

    const handleSearch = async () => {
        // Normal arama + hafıza araması
        const memoryResults = await searchMemories(query);
        setMemoryResults(memoryResults);

        // Burada normal arama sonuçlarıyla birleştir
    };

    return (
        <div className="enhanced-search">
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Arama yapin... (yapay hafiza destekli)"
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />

            {/* Hafıza önerileri */}
            {memoryResults.length > 0 && (
                <div className="memory-suggestions">
                    <h4>Hafızadan Öneriler:</h4>
                    {memoryResults.map((item, index) => (
                        <div key={index} className="memory-item">
                            {item.file_path} - {item.similarity_score}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default EnhancedSearch;