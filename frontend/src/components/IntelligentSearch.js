import React, { useState, useEffect, useCallback } from 'react';
import { useMemory } from '../contexts/MemoryContext';
import './IntelligentSearch.css';

const IntelligentSearch = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const { searchMemories, trackActivity, fetchSuggestions } = useMemory();

    // Debounced search
    useEffect(() => {
        const delayDebounceFn = setTimeout(async () => {
            if (query.length > 2) {
                setIsLoading(true);

                // Aktiviteyi takip et
                await trackActivity('search_query', { query });

                // Semantic arama yap
                const searchResults = await searchMemories(query);
                setResults(searchResults.semantic_results || []);

                // Behavioral önerileri göster
                setSuggestions(searchResults.behavioral_suggestions || []);

                setIsLoading(false);
            }
        }, 300);

        return () => clearTimeout(delayDebounceFn);
    }, [query, searchMemories, trackActivity]);

    // Context önerilerini al
    useEffect(() => {
        const loadContextSuggestions = async () => {
            if (query.length === 0) {
                const contextSuggestions = await fetchSuggestions();
                setSuggestions(contextSuggestions);
            }
        };

        loadContextSuggestions();
    }, [query, fetchSuggestions]);

    return (
        <div className="intelligent-search">
            <div className="search-box">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="🔍 Akıllı arama... (yapay hafıza destekli)"
                    className="search-input"
                />
                {isLoading && <div className="loading-spinner"></div>}
            </div>

            {/* Context Önerileri */}
            {suggestions.length > 0 && query.length === 0 && (
                <div className="context-suggestions">
                    <h4>Size Özel Öneriler</h4>
                    {suggestions.map((suggestion, index) => (
                        <div key={index} className="suggestion-item">
                            <div className="suggestion-badge">{suggestion.type}</div>
                            <span className="suggestion-text">{suggestion.reason}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Arama Sonuçları */}
            {results.length > 0 && (
                <div className="search-results">
                    <h4>Semantic Eşleşmeler</h4>
                    {results.map((result, index) => (
                        <div key={index} className="result-item">
                            <div className="result-header">
                                <span className="filename">{result.file_path.split('/').pop()}</span>
                                <span className="confidence">
                                    %{Math.round(result.similarity_score * 100)} eşleşme
                                </span>
                            </div>
                            <div className="result-meta">
                                <span>Son erişim: {new Date(result.last_accessed).toLocaleDateString()}</span>
                                <span>Erişim sayısı: {result.access_count}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Behavioral Öneriler */}
            {suggestions.length > 0 && query.length > 0 && (
                <div className="behavioral-suggestions">
                    <h4>İlgili Öneriler</h4>
                    {suggestions.map((suggestion, index) => (
                        <div key={index} className="suggestion-item">
                            {suggestion.content}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default IntelligentSearch;
