import React, { useState } from 'react';
import './SearchEngine.css'; // Mevcut CSS'i kullanabiliriz veya özelleştirebiliriz

const SemanticMemoryInput = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setIsSearching(true);
        try {
            // Backend'deki semantic search endpoint'ine istek
            const response = await fetch('/api/memory/search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ query: query })
            });

            const data = await response.json();
            // Backend'den gelen sonuçları set et
            setResults(data);
        } catch (error) {
            console.error("Arama hatası:", error);
        } finally {
            setIsSearching(false);
        }
    };

    return (
        <div className="semantic-memory-wrapper" style={{ marginTop: '20px', padding: '20px', background: '#1e1e1e', borderRadius: '12px' }}>
            <h2 style={{ color: '#fff', marginBottom: '15px' }}>Yapay Hafıza & Semantik Arama</h2>

            <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px' }}>
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Hafızada ne aramak istersin? (Örn: Geçen hafta Java projesinde ne yaptım?)"
                    style={{
                        flex: 1,
                        padding: '12px',
                        borderRadius: '8px',
                        border: '1px solid #444',
                        background: '#2a2a2a',
                        color: '#fff'
                    }}
                />
                <button
                    type="submit"
                    disabled={isSearching}
                    style={{
                        padding: '12px 24px',
                        borderRadius: '8px',
                        background: '#007bff',
                        color: 'white',
                        border: 'none',
                        cursor: 'pointer'
                    }}
                >
                    {isSearching ? 'Aranıyor...' : 'Hatırla'}
                </button>
            </form>

            {/* Sonuç Alanı */}
            {results.length > 0 && (
                <div className="search-results" style={{ marginTop: '20px' }}>
                    <h4 style={{ color: '#ccc', marginBottom: '10px' }}>Bulunan Anlamsal Eşleşmeler:</h4>
                    <div style={{ display: 'grid', gap: '10px' }}>
                        {results.map((item, idx) => (
                            <div key={idx} style={{ padding: '10px', background: '#252525', borderRadius: '6px', borderLeft: '3px solid #00d26a' }}>
                                <div style={{ fontWeight: 'bold', color: '#fff' }}>{item.file_name}</div>
                                <div style={{ fontSize: '0.9rem', color: '#aaa' }}>
                                    Benzerlik: %{(item.similarity_score * 100).toFixed(1)}
                                </div>
                                <div style={{ fontSize: '0.85rem', color: '#888', marginTop: '4px' }}>
                                    {item.content_summary || 'Özet bilgisi yok.'}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default SemanticMemoryInput;