import React, { useState, useEffect } from 'react';
import './TrendingView.css'; // CSS dosyasını import ediyoruz

const TrendingView = () => {
    const [trendingFiles, setTrendingFiles] = useState([]);
    const [activeCategory, setActiveCategory] = useState('all');
    const [loading, setLoading] = useState(false);
    const [isDarkTheme, setIsDarkTheme] = useState(true);

    useEffect(() => {
        fetchTrendingFiles();
    }, [activeCategory]);

    const fetchTrendingFiles = async () => {
        try {
            console.log('🔥 Trend verileri çekiliyor...');
            const token = localStorage.getItem('token');

            const response = await fetch('http://localhost:8001/api/trending/', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            console.log('📡 Trend response status:', response.status);

            if (!response.ok) {
                // 500 hatası durumunda fallback data kullan
                if (response.status === 500) {
                    console.warn('⚠️ Trend API 500 hatası, fallback data kullanılıyor');
                    setTrendingFiles([]);
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ Trend verisi:', data);
            setTrendingFiles(data);
        } catch (error) {
            console.error('❌ Trend verileri yüklenirken hata:', error);
            // Hata durumunda boş array ile devam et
            setTrendingFiles([]);
        }
    };

    const toggleTheme = () => {
        setIsDarkTheme(!isDarkTheme);
    };

    const getCategoryLabel = (category) => {
        switch (category) {
            case 'all': return 'Tümü';
            case 'image': return 'Görseller';
            case 'video': return 'Videolar';
            case 'document': return 'Dokümanlar';
            case 'audio': return 'Sesler';
            default: return category;
        }
    };

    const getFileIcon = (fileType) => {
        switch (fileType) {
            case 'image': return '🖼️';
            case 'video': return '🎥';
            case 'document': return '📄';
            case 'audio': return '🎵';
            default: return '📁';
        }
    };

    return (
        <div className={`trending-container ${isDarkTheme ? '' : 'light-theme'}`}>
            <header className="trending-header">
                <div className="logo">
                    <i className="fas fa-chart-line"></i>
                    <span>Trendler</span>
                </div>
                <button className="theme-toggle" onClick={toggleTheme}>
                    <i className={isDarkTheme ? 'fas fa-moon' : 'fas fa-sun'}></i>
                </button>
            </header>

            <main>
                <h1>Trend İçerikler</h1>
                <p className="subtitle">En popüler ve güncel içerikleri keşfedin</p>

                <div className="filter-tabs">
                    {['all', 'image', 'video', 'document', 'audio'].map(category => (
                        <div
                            key={category}
                            className={`filter-tab ${activeCategory === category ? 'active' : ''}`}
                            onClick={() => setActiveCategory(category)}
                        >
                            {getCategoryLabel(category)}
                        </div>
                    ))}
                </div>

                {loading ? (
                    <div className="content-area">
                        <div className="loading">
                            <i className="fas fa-spinner fa-spin"></i>
                            <p>Yükleniyor...</p>
                        </div>
                    </div>
                ) : (
                    <div className="content-area">
                        {trendingFiles.length > 0 ? (
                            <div className="trending-grid">
                                {trendingFiles.map(file => (
                                    <div key={file.id} className="trending-item">
                                        <div className="trending-thumbnail">
                                            {file.file_type === 'image' ? (
                                                <img src={file.share_url} alt={file.file_name} />
                                            ) : (
                                                <div className="file-icon">
                                                    {getFileIcon(file.file_type)}
                                                </div>
                                            )}
                                            <div className="trending-badge">
                                                🔥 {Math.round(file.trend_score || 0)}
                                            </div>
                                        </div>
                                        <div className="trending-info">
                                            <h4>{file.file_name}</h4>
                                            <p><i className="fas fa-user"></i> {file.created_by_username || 'Anonim'}</p>
                                            <p><i className="fas fa-eye"></i> {file.view_count || 0} görüntülenme</p>
                                            <p><i className="fas fa-clock"></i> {file.upload_time_ago}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <i className="far fa-folder-open"></i>
                                <h2>Henüz trend içerik bulunmuyor</h2>
                                <p>Şu anda hiç trend içerik yok. Daha sonra tekrar kontrol etmeyi unutmayın veya yeni içerik ekleyin.</p>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
};

export default TrendingView;