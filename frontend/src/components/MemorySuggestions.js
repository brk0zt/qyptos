// frontend/src/components/MemorySuggestions.js
import React, { useState, useEffect } from 'react';
import { useMemory } from '../contexts/MemoryContext';

const MemorySuggestions = () => {
    const { suggestions, fetchSuggestions } = useMemory();
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        // Component mount olduğunda önerileri getir
        fetchSuggestions();

        // Her 30 saniyede bir önerileri güncelle
        const interval = setInterval(fetchSuggestions, 30000);
        return () => clearInterval(interval);
    }, [fetchSuggestions]);

    if (suggestions.length === 0 || !isVisible) {
        return (
            <button
                className="suggestions-toggle"
                onClick={() => setIsVisible(!isVisible)}
            >
                💡 Önerileri Göster ({suggestions.length})
            </button>
        );
    }

    return (
        <div className="memory-suggestions-panel">
            <div className="panel-header">
                <h3>Yapay Hafıza Önerileri</h3>
                <button onClick={() => setIsVisible(false)}>✕</button>
            </div>
            <div className="suggestions-list">
                {suggestions.map((suggestion, index) => (
                    <div key={index} className="suggestion-item">
                        <div className="suggestion-type">{suggestion.type}</div>
                        <div className="suggestion-content">{suggestion.content}</div>
                        <div className="suggestion-confidence">
                            %{Math.round(suggestion.confidence * 100)} eşleşme
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default MemorySuggestions;