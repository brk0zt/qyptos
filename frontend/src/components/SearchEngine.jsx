import React, { useState, useEffect, useRef } from 'react';
import './SearchEngine.css'; // Gerekli CSS dosyası

const SearchEngine = () => {
    const videoRefs = useRef(new Map());
    const videoTimeoutRef = useRef(null); // Timeout ID'yi tutmak için
    const [query, setQuery] = useState('');
    const [searchType, setSearchType] = useState('all');
    const [results, setResults] = useState({ fileshares: [] });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [hasSearched, setHasSearched] = useState(false);
    const [activeVideoPreview, setActiveVideoPreview] = useState(null); // ✅ Move useState to top level

    // DEBUG: Dosya kontrolü (Yerinde Kalmalı)
    useEffect(() => {
        const checkPublicFiles = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch('http://localhost:8001/api/files/', {
                    headers: { 'Authorization': `Bearer ${token}` },
                });
                if (response.ok) {
                    const files = await response.json();
                    console.log('Kullanıcı dosyaları:', files);
                }
            } catch (error) {
                console.error('Dosya kontrol hatası:', error);
            }
        };
        checkPublicFiles();
    }, []);

    const setVideoRef = (fileId, element) => {
        if (element) {
            videoRefs.current.set(fileId, element);
        } else {
            videoRefs.current.delete(fileId);
        }
    };

    const handleVideoMouseEnter = (fileId) => {
        const videoElement = videoRefs.current.get(fileId);

        if (videoElement) {
            // Önceki zamanlayıcıyı temizle
            if (videoTimeoutRef.current) {
                clearTimeout(videoTimeoutRef.current);
            }

            // Oynatmayı dene
            videoElement.play().catch(e => console.log("Video Play Error:", e));

            // 5 saniye sonra durdurma mantığını ayarla
            videoTimeoutRef.current = setTimeout(() => {
                // Eğer video hala bu element ise durdur.
                if (videoElement) {
                    videoElement.pause();
                    videoElement.currentTime = 0; // Başa sar
                }
            }, 5000); // 5 saniye
        }
    };

    // 3. Fare Video Alanından Çıktığında
    const handleVideoMouseLeave = (fileId) => {
        const videoElement = videoRefs.current.get(fileId);

        if (videoElement) {
            // Zamanlayıcıyı hemen temizle
            if (videoTimeoutRef.current) {
                clearTimeout(videoTimeoutRef.current);
            }

            // Durdur ve başa sar
            videoElement.pause();
            videoElement.currentTime = 0;
        }
    };

    // ✅ YARDIMCI FONKSİYON: Dosya Tipine Göre İkon Belirleme
    const getFileIcon = (fileName) => {
        if (!fileName) return 'fa-file';
        const ext = fileName.split('.').pop().toLowerCase();
        const iconMap = {
            jpg: 'fa-file-image',
            jpeg: 'fa-file-image',
            png: 'fa-file-image',
            gif: 'fa-file-image',
            pdf: 'fa-file-pdf',
            doc: 'fa-file-word',
            docx: 'fa-file-word',
            xls: 'fa-file-excel',
            xlsx: 'fa-file-excel',
            ppt: 'fa-file-powerpoint',
            pptx: 'fa-file-powerpoint',
            zip: 'fa-file-archive',
            rar: 'fa-file-archive',
            mp3: 'fa-file-audio',
            wav: 'fa-file-audio',
            mp4: 'fa-file-video',
            avi: 'fa-file-video',
            txt: 'fa-file-alt',
            js: 'fa-file-code',
            html: 'fa-file-code',
            css: 'fa-file-code',
            default: 'fa-file'
        };
        return iconMap[ext] || iconMap.default;
    };

    // ✅ YENİ YARDIMCI FONKSİYON: Dosya tipine göre önizleme içeriğini oluşturan fonksiyon
    const renderFilePreview = (fileShare) => {
        const previewSrc = fileShare.preview_url || fileShare.file_url;

        const fileExtension = fileShare.file_name ? fileShare.file_name.split('.').pop().toLowerCase() : '';
        const isImage = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(fileExtension);
        const isVideo = ['mp4', 'mov', 'avi', 'wmv', 'flv', 'webm'].includes(fileExtension);
        const isAudio = ['mp3', 'wav', 'ogg', 'aac'].includes(fileExtension);
        const isPdf = ['pdf'].includes(fileExtension);

        if (isImage && previewSrc) {
            return (
                <div className="file-preview-content">
                    <img
                        src={previewSrc}
                        alt={fileShare.file_name}
                        className="preview-image-tag"
                    />
                </div>
            );
        }

        if (isVideo && previewSrc) {
            return (
                <div
                    className="file-preview-content"
                    onMouseEnter={() => handleVideoMouseEnter(fileShare.id)}
                    onMouseLeave={() => handleVideoMouseLeave(fileShare.id)}
                >
                    <video
                        ref={el => setVideoRef(fileShare.id, el)}
                        muted
                        loop={false}
                        preload="metadata"
                        className="preview-video"
                    >
                        <source src={previewSrc} type={`video/${fileExtension}`} />
                    </video>
                </div>
            );
        } else if (isAudio) {
            return (
                <div className="file-preview-content audio-preview">
                    <div className="preview-icon-large">
                        <i className="fas fa-music"></i>
                    </div>
                </div>
            );
        } else if (isPdf && previewSrc) {
            return (
                <div className="file-preview-content pdf-preview">
                    <iframe
                        src={previewSrc}
                        title={fileShare.file_name}
                        className="preview-iframe"
                    />
                </div>
            );
        } else {
            return (
                <div className="file-preview-content document-preview">
                    <div className={`preview-icon-large`}>
                        <i className={`fas ${getFileIcon(fileShare.file_name)}`}></i>
                    </div>
                </div>
            );
        }
    };

    // 1. ✅ YARDIMCI FONKSİYON: Arama Sonuçlarını Temizle
    const handleClear = () => {
        setQuery('');
        setResults({ fileshares: [] });
        setHasSearched(false);
        setError('');
    };

    // 2. ✅ ANA FONKSİYON: Arama İşlemi (API ve JSON Hata Çözümleri Dahil)
    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError('');
        setHasSearched(true);

        try {
            const token = localStorage.getItem('token');

            const response = await fetch(
                `http://localhost:8001/api/search/?q=${encodeURIComponent(query)}`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Arama hatası: ${errorData.message || response.status}`);
            }

            const data = await response.json();

            const searchResults = data.results || data;

            const allFiles = [
                ...(searchResults.files || []),
                ...(searchResults.group_files || [])
            ];

            setResults({ fileshares: allFiles });

        } catch (err) {
            console.error('Arama sırasında bir hata oluştu:', err);
            setError(err.message || 'Arama sırasında beklenmeyen bir hata oluştu.');
            setResults({ fileshares: [] });
        } finally {
            setLoading(false);
        }
    };

    // 3. ✅ RENDER FONKSİYONU: Önizleme ve Tasarım
    const renderSearchResults = () => {
        const { fileshares } = results;

        if (loading) {
            return <div className="loading-state">🔍 Herkese Açık Dosyalar Aranıyor...</div>;
        }

        if (fileshares.length === 0) {
            return (
                <div className="no-results">
                    <div className="no-results-icon">🤷‍♂️</div>
                    <h3>Sonuç bulunamadı</h3>
                    <p>Aradığınız anahtar kelimeye uygun herkese açık dosya bulunamadı.</p>
                </div>
            );
        }

        return (
            <div className="results-grid">
                {fileshares.map((fileShare) => {
                    let clickUrl = fileShare.share_url || fileShare.file_url || '#';
                    if (clickUrl !== '#' && !clickUrl.endsWith('/')) {
                        clickUrl += '/'; // 🚨 URL'nin sonuna eğik çizgiyi ekle
                    }
                    return (
                        <div
                            key={fileShare.id}
                            className="result-card"
                            onClick={() => {
                                if (clickUrl && clickUrl !== '#') {
                                    window.open(clickUrl, '_blank');
                                } else {
                                    console.warn("Tıklama için geçerli URL bulunamadı.");
                                }
                            }}>

                            {/* ✅ DOSYA ÖNİZLEME ALANI */}
                            <div className="file-preview-container">
                                {renderFilePreview(fileShare)}
                            </div>

                            {/* DOSYA BİLGİ ALANI */}
                            <div className="result-content">
                                <h4 title={fileShare.file_name}>{fileShare.file_name}</h4>

                                <p className="file-owner"><i className="fas fa-user"></i> {fileShare.created_by_username || 'Anonim'}</p>

                                <div className="file-stats">
                                    <span className="stat"><i className="fas fa-clock"></i> {fileShare.upload_time_ago || 'Tarih Yok'}</span>
                                    <span className="stat"><i className="fas fa-eye"></i> {fileShare.view_count || 0}</span>
                                </div>

                                <div className="file-badges">
                                    {fileShare.is_one_time_view && (
                                        <span className="badge badge-one-time">Tek Gösterimlik</span>
                                    )}
                                    {fileShare.is_password_protected && (
                                        <span className="badge badge-password">Şifreli</span>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    // Component Return
    return (
        <div className="search-engine" data-theme="dark">
            <header className="search-header">
                <h2>Herkese Açık Dosya Arama Motoru</h2>
                <p>Milyonlarca paylaşılan dosya arasında arama yapın.</p>
            </header>

            <form className="search-form" onSubmit={handleSearch}>
                <div className="search-input-group">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Dosya adı, kullanıcı adı..."
                        className="search-input"
                    />

                    <button type="submit" className="search-btn" disabled={loading || !query.trim()}>
                        {loading ? '🔍 Aranıyor...' : '🔍 Ara'}
                    </button>
                    {hasSearched && (
                        <button type="button" onClick={handleClear} className="clear-btn">
                            ✖ Temizle
                        </button>
                    )}
                </div>
            </form>

            {error && (
                <div className="error-message">
                    ❌ {error}
                </div>
            )}

            <div className="search-results">
                {hasSearched || loading ? (
                    renderSearchResults()
                ) : (
                    <div className="search-placeholder">
                        <div className="placeholder-icon">🔍</div>
                        <h3>Arama yapın</h3>
                        <p>Herkese açık dosyaları bulmak için yukarıdan arama yapın.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SearchEngine;