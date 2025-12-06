import React, { useState, useEffect } from "react";
import { useAuth } from "../AuthContext";
import "./ChunkDownloader.css";
import SecureViewer from './SecureViewer';

const BrainMemoryVisualization = ({ percentage, used, remaining }) => {
    return (
        <div className="brain-memory">
            <h3>🧠 Yapay Hafıza</h3>
            <div className="brain-container">
                <div className="brain-fill-container">
                    <div
                        className="brain-fill"
                        style={{ height: `${percentage}%` }}
                    ></div>
                </div>
                <div className="brain-image"></div>
                <div className="brain-percentage">
                    {percentage.toFixed(1)}%
                </div>
            </div>
            <div className="memory-info">
                <div className="info-item">
                    <div className="info-value">{used.toFixed(1)} GB</div>
                    <div className="info-label">Kullanılan</div>
                </div>
                <div className="info-item">
                    <div className="info-value">{remaining.toFixed(1)} GB</div>
                    <div className="info-label">Kalan</div>
                </div>
            </div>
        </div>
    );
};

const StoragePieChart = ({ percentage, used, remaining }) => {
    return (
        <div className="storage-pie">
            <h3>💾 Depolama Alanı</h3>
            <div
                className="pie-chart"
                style={{ '--percentage': `${percentage}%` }}
            >
                <span className="percentage">{percentage.toFixed(1)}%</span>
            </div>
            <div className="memory-info">
                <div className="info-item">
                    <div className="info-value">{used} GB</div>
                    <div className="info-label">Kullanılan</div>
                </div>
                <div className="info-item">
                    <div className="info-value">{remaining} GB</div>
                    <div className="info-label">Kalan</div>
                </div>
            </div>
        </div>
    );
};

const ChunkDownloader = ({ apiBase, userEmail }) => {
    const { user, logout } = useAuth();
    const [files, setFiles] = useState([]);
    const [canDownload, setCanDownload] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [viewOption, setViewOption] = useState('standard');
    const [privacyOption, setPrivacyOption] = useState('private');
    const [totalStorage, setTotalStorage] = useState(0);
    const [viewDuration, setViewDuration] = useState('10s');
    const [sharingFile, setSharingFile] = useState(null);
    const [shareLinks, setShareLinks] = useState([]);
    const [memoryUsage, setMemoryUsage] = useState(0);
    const [viewingFile, setViewingFile] = useState(null); // Yeni state: görüntülenen dosya

    const viewDurationOptions = [
        { value: '10s', label: '10 Saniye', description: 'Medya 10 saniye görüntülendikten sonra kapanır' },
        { value: '30s', label: '30 Saniye', description: 'Medya 30 saniye görüntülendikten sonra kapanır' },
        { value: '1m', label: '1 Dakika', description: 'Medya 1 dakika görüntülendikten sonra kapanır' },
        { value: '5m', label: '5 Dakika', description: 'Medya 5 dakika görüntülendikten sonra kapanır' },
        { value: '1h', label: '1 Saat', description: 'Medya 1 saat görüntülendikten sonra kapanır' },
        { value: 'video', label: 'Video Süresi', description: 'Sadece video süresi boyunca görüntülenir' },
        { value: 'unlimited', label: 'Süresiz', description: 'Manuel olarak kapatılana kadar açık kalır' },
    ];

    const getToken = () => {
        const token = localStorage.getItem('token');
        if (!token) {
            console.log('❌ Token bulunamadı');
            return null;
        }
        return token;
    };

    const getBaseUrl = () => {
        return apiBase.replace('/api', '');
    };

    const getShareUrl = (file) => {
        // ÖNEMLİ: file.view_token kullanıyoruz!
        const baseUrl = getBaseUrl();
        return `${baseUrl}/share/${file.view_token}/`;
    };

    useEffect(() => {
        const interval = setInterval(() => {
            setMemoryUsage(Math.random() * 8 + 2);
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchFiles = async () => {
        const token = getToken();
        if (!token) {
            logout();
            return;
        }

        try {
            console.log('🔄 Dosyalar çekiliyor...');
            const response = await fetch(`${apiBase}/files/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                }
            });

            console.log('📡 Dosya response status:', response.status);

            if (response.ok) {
                const userFiles = await response.json();
                console.log('✅ Dosya verisi:', userFiles);
                setFiles(userFiles);

                let totalSize = 0;
                userFiles.forEach(file => {
                    if (file.file_size && file.file_size > 0) {
                        totalSize += file.file_size;
                    } else {
                        const fileName = file.file_name || (file.file ? file.file.split('/').pop().toLowerCase() : '');
                        if (fileName.match(/\.(jpg|jpeg|png|gif|bmp|webp)$/)) {
                            totalSize += 500 * 1024;
                        } else {
                            totalSize += 1024 * 1024;
                        }
                    }
                });
                setTotalStorage(totalSize);
            } else if (response.status === 401) {
                console.log('❌ Token geçersiz');
                logout();
            } else if (response.status === 500) {
                console.error('❌ Sunucu hatası:', response.status);
                const errorText = await response.text();
                console.error('Sunucu hata detayı:', errorText);
                alert('Sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin.');
            } else {
                console.log('⚠️ Dosyalar alınamadı, status:', response.status);
                setFiles([]);
            }
        } catch (error) {
            console.error('❌ Dosyalar yüklenirken hata:', error);
            setFiles([]);
        }
    };

    useEffect(() => {
        fetchFiles();
    }, []);

    // handleFileUpload fonksiyonunu düzgün şekilde tanımla
    const handleFileUpload = async (e) => {
        e.preventDefault();

        const token = getToken();
        if (!token) {
            alert('Oturumunuz sona ermiş. Lütfen tekrar giriş yapın.');
            logout();
            return;
        }

        if (!selectedFile) {
            alert("Lütfen bir dosya seçin");
            return;
        }

        // Dosya boyutu kontrolü (10 GB)
        const maxSize = 10 * 1024 * 1024 * 1024;
        if (selectedFile.size > maxSize) {
            alert('Dosya boyutu çok büyük! Maksimum 10 GB dosya yükleyebilirsiniz.');
            return;
        }

        // Toplam depolama kontrolü
        if (totalStorage + selectedFile.size > maxSize) {
            alert('Depolama alanı yetersiz! Lütfen bazı dosyaları silin.');
            return;
        }

        setUploading(true);

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('can_download', canDownload);
        formData.append('one_time_view', viewOption === 'one_time');
        formData.append('is_public', privacyOption === 'public');

        // Görüntüleme süresini ekle
        if (viewOption === 'one_time') {
            formData.append('view_duration', viewDuration);
        }

        try {
            const response = await fetch(`${apiBase}/files/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                alert('Dosya başarıyla yüklenmiştir!');
                setSelectedFile(null);
                setViewOption('standard');
                setViewDuration('10s');
                setPrivacyOption('private');
                if (document.getElementById('file-input')) {
                    document.getElementById('file-input').value = '';
                }
                fetchFiles();
            } else if (response.status === 401) {
                alert('Oturumunuz sona ermiş. Lütfen tekrar giriş yapın.');
                logout();
            } else {
                alert('Dosya yüklenirken bir hata oluştu. Lütfen tekrar deneyin.');
            }
        } catch (error) {
            console.error('❌ Yükleme hatası:', error);
            alert('Dosya yüklenirken bağlantı hatası oluştu');
        } finally {
            setUploading(false);
        }
    };

    const handleDeleteFile = async (fileId) => {
        const token = getToken();
        if (!token) {
            alert('Oturumunuz sona ermiş. Lütfen tekrar giriş yapın.');
            logout();
            return;
        }

        if (!confirm('Bu dosyayı silmek istediğinizden emin misiniz?')) {
            return;
        }

        try {
            const response = await fetch(`${apiBase}/files/${fileId}/`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });

            if (response.ok) {
                alert('Dosya başarıyla silindi');
                fetchFiles();
            } else if (response.status === 401) {
                logout();
            } else {
                alert('Silme işlemi başarısız: ' + response.status);
            }
        } catch (error) {
            console.error('Silme hatası:', error);
            alert('Dosya silinirken hata oluştu');
        }
    };

    const handleDownloadFile = async (file) => {
        const token = getToken();
        if (!token) {
            alert('Oturumunuz sona ermiş. Lütfen tekrar giriş yapın.');
            logout();
            return;
        }

        try {
            let fileUrl;

            if (file.file_url) {
                fileUrl = file.file_url;
            }
            else if (file.file) {
                if (file.file.startsWith('http')) {
                    fileUrl = file.file;
                } else if (file.file.startsWith('/')) {
                    const baseUrl = getBaseUrl();
                    fileUrl = `${baseUrl}${file.file}`;
                }
            }
            else {
                fileUrl = `${apiBase}/files/${file.id}/download/`;
            }

            console.log('📥 İndirme URL:', fileUrl);
            window.open(fileUrl, '_blank');
        } catch (error) {
            console.error('İndirme hatası:', error);
            alert('Dosya indirilirken hata oluştu');
        }
    };

    const handleViewFile = (file) => {
        // Dosyayı görüntüleme modunda aç
        setViewingFile(file);
    };

    const handleCloseViewer = () => {
        // Görüntüleyiciyi kapat
        setViewingFile(null);
    };

    // Paylaşım fonksiyonları
    const fetchShareLinks = async (fileId) => {
        const token = getToken();
        try {
            const response = await fetch(`${apiBase}/shares/?file=${fileId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });
            if (response.ok) {
                const shares = await response.json();
                setShareLinks(shares);
            }
        } catch (error) {
            console.error('Paylaşım linkleri yüklenemedi:', error);
        }
    };

    const createShareLink = async (fileId, shareType, expiresHours = 24, maxViews = 1, password = '') => {
        const token = getToken();
        try {
            const shareData = {
                file: fileId,
                share_type: shareType,
                max_views: maxViews
            };

            if (expiresHours) {
                const expiresAt = new Date();
                expiresAt.setHours(expiresAt.getHours() + expiresHours);
                shareData.expires_at = expiresAt.toISOString();
            }

            if (password) {
                shareData.password = password;
            }

            const response = await fetch(`${apiBase}/shares/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(shareData)
            });

            if (response.ok) {
                const newShare = await response.json();
                setShareLinks(prev => [...prev, newShare]);
                return newShare;
            }
        } catch (error) {
            console.error('Paylaşım oluşturulamadı:', error);
        }
        return null;
    };

    const revokeShare = async (shareId) => {
        const token = getToken();
        try {
            const response = await fetch(`${apiBase}/shares/${shareId}/revoke/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });

            if (response.ok) {
                setShareLinks(prev => prev.filter(share => share.id !== shareId));
            }
        } catch (error) {
            console.error('Paylaşım iptal edilemedi:', error);
        }
    };

    const handleShareClick = async (file) => {
        // Debug için
        console.log('🔗 Paylaşım dosyası:', file);

        const shareUrl = getShareUrl(file);

        // Linki kopyala ve bilgi ver
        navigator.clipboard.writeText(shareUrl);
        alert(`✅ Paylaşım linki kopyalandı!\n\nLink: ${shareUrl}\n\nBu linki istediğiniz kişiyle paylaşabilirsiniz.`);

        // Modal'ı kapat
        setSharingFile(null);
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text).then(() => {
            alert('Link panoya kopyalandı!');
        });
    };

    const shareOnWhatsApp = (url) => {
        const text = `Dosyayı görüntüle: ${url}`;
        window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
    };

    const shareOnInstagram = (url) => {
        const text = `Bu dosyayı görüntüle: ${url}`;
        window.open(`https://instagram.com/direct?text=${encodeURIComponent(text)}`, '_blank');
    };

    const shareOnCloudDM = (share) => {
        alert(`Cloud DM paylaşımı: ${share.share_url}\nBu özellik uygulamanızın mesajlaşma sistemine entegre edilebilir.`);
    };

    const getFileIcon = (file) => {
        const fileName = file.file_name || (file.file ? file.file.split('/').pop().toLowerCase() : '');

        if (file.one_time_view) {
            return 'fas fa-lock';
        }

        if (fileName.match(/\.(jpg|jpeg|png|gif|bmp|webp|svg)$/)) {
            return 'fas fa-image';
        } else if (fileName.match(/\.(mp4|avi|mov|wmv|flv|mkv)$/)) {
            return 'fas fa-video';
        } else if (fileName.match(/\.(mp3|wav|ogg|flac)$/)) {
            return 'fas fa-music';
        } else if (fileName.match(/\.(pdf)$/)) {
            return 'fas fa-file-pdf';
        } else if (fileName.match(/\.(doc|docx)$/)) {
            return 'fas fa-file-word';
        } else if (fileName.match(/\.(xls|xlsx)$/)) {
            return 'fas fa-file-excel';
        } else if (fileName.match(/\.(zip|rar|7z|tar|gz)$/)) {
            return 'fas fa-file-archive';
        } else if (fileName.match(/\.(exe|msi)$/)) {
            return 'fas fa-cog';
        } else if (fileName.match(/\.(txt|rtf)$/)) {
            return 'fas fa-file-alt';
        } else {
            return 'fas fa-file';
        }
    };

    const getFilePreview = (file) => {
        const fileName = file.file_name || (file.file ? file.file.split('/').pop().toLowerCase() : '');
        const isImage = fileName.match(/\.(jpg|jpeg|png|gif|bmp|webp|svg)$/);

        console.log('🔍 Preview için dosya analizi:', {
            fileName,
            isImage,
            file_url: file.file_url,
            file: file.file,
            id: file.id
        });

        if (!isImage) {
            return null;
        }

        // Öncelikle doğrudan file_url'i kullan
        if (file.file_url) {
            console.log('✅ file_url kullanılıyor:', file.file_url);
            return file.file_url;
        }

        // Sonra file alanını kullan
        if (file.file) {
            console.log('✅ file alanı kullanılıyor:', file.file);
            return file.file;
        }

        console.log('❌ Hiçbir URL yöntemi çalışmadı');
        return null;
    };

    // Thumbnail gösterimini iyileştiren CSS
    const thumbnailStyles = `
.file-preview {
    position: relative;
    width: 100%;
    height: 120px;
    background: #f8fafc;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
    overflow: hidden;
    border: 1px solid #e5e7eb;
    cursor: pointer;
}

.file-thumbnail {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: all 0.3s ease;
}

.file-thumbnail:hover {
    transform: scale(1.05);
}

.file-icon.fallback {
    font-size: 2.5rem;
    color: #6b7280;
}

.one-time-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(239, 68, 68, 0.9);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    z-index: 2;
}

/* Tıklanabilir dosya kartı */
.file-card {
    cursor: pointer;
    transition: all 0.3s ease;
}

.file-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

/* Dosya bilgisi için pointer events none */
.file-info, .file-actions {
    pointer-events: none;
}

/* Butonlar için pointer events auto */
.file-actions .btn {
    pointer-events: auto;
}
`;

    // CSS'i head'e ekle
    useEffect(() => {
        const style = document.createElement('style');
        style.textContent = thumbnailStyles;
        document.head.appendChild(style);
        return () => {
            document.head.removeChild(style);
        };
    }, []);

    // Paylaşım modal'ı
    const renderShareModal = () => {
        if (!sharingFile) return null;

        return (
            <div className="modal-overlay">
                <div className="share-modal">
                    <div className="modal-header">
                        <h3>📤 Dosyayı Paylaş</h3>
                        <button onClick={() => setSharingFile(null)} className="close-btn">
                            <i className="fas fa-times"></i>
                        </button>
                    </div>

                    <div className="modal-content">
                        {/* Yeni paylaşım oluşturma */}
                        <div className="create-share-section">
                            <h4>Yeni Paylaşım Oluştur</h4>
                            <div className="share-options">
                                <button
                                    onClick={() => createShareLink(sharingFile.id, 'public')}
                                    className="share-option-btn"
                                >
                                    <i className="fas fa-globe"></i>
                                    <span>Herkese Açık Link</span>
                                    <small>Herkes görüntüleyebilir</small>
                                </button>

                                <button
                                    onClick={() => createShareLink(sharingFile.id, 'one_time', 24, 1)}
                                    className="share-option-btn"
                                >
                                    <i className="fas fa-eye"></i>
                                    <span>Tek Kullanımlık</span>
                                    <small>Sadece 1 kez görüntülenebilir</small>
                                </button>

                                <button
                                    onClick={() => {
                                        const password = prompt('Şifre belirleyin:');
                                        if (password) {
                                            createShareLink(sharingFile.id, 'private', 168, 10, password);
                                        }
                                    }}
                                    className="share-option-btn"
                                >
                                    <i className="fas fa-lock"></i>
                                    <span>Şifreli Paylaşım</span>
                                    <small>Şifre gerektirir</small>
                                </button>
                            </div>
                        </div>

                        {/* Aktif paylaşımlar */}
                        <div className="active-shares-section">
                            <h4>Aktif Paylaşımlar</h4>
                            {shareLinks.length === 0 ? (
                                <p className="no-shares">Henüz paylaşım linki oluşturulmamış</p>
                            ) : (
                                <div className="shares-list">
                                    {shareLinks.map(share => (
                                        <div key={share.id} className="share-item">
                                            <div className="share-info">
                                                <div className="share-type">
                                                    <i className={`fas ${share.share_type === 'public' ? 'fa-globe' :
                                                        share.share_type === 'one_time' ? 'fa-eye' : 'fa-lock'
                                                        }`}></i>
                                                    {share.share_type}
                                                </div>
                                                <div className="share-stats">
                                                    Görüntülenme: {share.view_count}/{share.max_views}
                                                </div>
                                            </div>
                                            <div className="share-url">
                                                <input
                                                    type="text"
                                                    value={share.share_url}
                                                    readOnly
                                                    className="url-input"
                                                />
                                                <div className="share-actions">
                                                    <button
                                                        onClick={() => copyToClipboard(share.share_url)}
                                                        className="action-btn copy"
                                                    >
                                                        <i className="fas fa-copy"></i>
                                                    </button>
                                                    <button
                                                        onClick={() => shareOnWhatsApp(share.share_url)}
                                                        className="action-btn whatsapp"
                                                    >
                                                        <i className="fab fa-whatsapp"></i>
                                                    </button>
                                                    <button
                                                        onClick={() => shareOnInstagram(share.share_url)}
                                                        className="action-btn instagram"
                                                    >
                                                        <i className="fab fa-instagram"></i>
                                                    </button>
                                                    <button
                                                        onClick={() => shareOnCloudDM(share)}
                                                        className="action-btn cloud"
                                                    >
                                                        <i className="fas fa-cloud"></i>
                                                    </button>
                                                    <button
                                                        onClick={() => revokeShare(share.id)}
                                                        className="action-btn delete"
                                                    >
                                                        <i className="fas fa-trash"></i>
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    // Dosya görüntüleyici modal'ı
    const renderFileViewer = () => {
        if (!viewingFile) return null;

        console.log("🔍 Modal açıldı - Dosya:", viewingFile);

        return (
            <div className="modal-overlay" style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                background: 'rgba(0,0,0,0.98)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 10000
            }}>
                <div style={{
                    background: '#0a0a0a',
                    borderRadius: '12px',
                    padding: '25px',
                    maxWidth: '95%',
                    maxHeight: '95%',
                    position: 'relative',
                    border: '3px solid #ff4444',
                    boxShadow: '0 0 50px rgba(255,0,0,0.3)'
                }}>
                    <button
                        onClick={handleCloseViewer}
                        style={{
                            position: 'absolute',
                            top: '15px',
                            right: '15px',
                            background: '#ff4444',
                            color: 'white',
                            border: 'none',
                            borderRadius: '50%',
                            width: '40px',
                            height: '40px',
                            cursor: 'pointer',
                            fontSize: '18px',
                            fontWeight: 'bold',
                            zIndex: 10001
                        }}
                    >
                        ✕
                    </button>

                    <div style={{
                        color: '#ff4444',
                        textAlign: 'center',
                        marginBottom: '15px',
                        fontSize: '16px',
                        fontWeight: 'bold'
                    }}>
                        {viewingFile.one_time_view ? "🔒 GÜVENLİ GÖRÜNTÜLEYİCİ" : "📁 NORMAL GÖRÜNTÜLEYİCİ"}
                    </div>

                    {/* ✅ MUTLAKA SecureViewer ile sarmala */}
                    <SecureViewer file={viewingFile}>
                        <div style={{
                            maxWidth: '100%',
                            maxHeight: '80vh',
                            borderRadius: '8px',
                            overflow: 'hidden',
                            background: '#000'
                        }}>
                            {viewingFile.file_name?.toLowerCase().endsWith('.mp4') ? (
                                <video
                                    src={getShareUrl(viewingFile)}
                                    controls
                                    style={{
                                        maxWidth: '100%',
                                        maxHeight: '70vh',
                                        display: 'block'
                                    }}
                                    onContextMenu={(e) => e.preventDefault()}
                                />
                            ) : (
                                <img
                                    src={getShareUrl(viewingFile)}
                                    alt={viewingFile.file_name}
                                    style={{
                                        maxWidth: '100%',
                                        maxHeight: '70vh',
                                        objectFit: 'contain',
                                        display: 'block'
                                    }}
                                    onContextMenu={(e) => e.preventDefault()}
                                />
                            )}
                        </div>
                    </SecureViewer>

                    <div style={{
                        color: '#fff',
                        textAlign: 'center',
                        marginTop: '15px',
                        fontSize: '12px',
                        opacity: 0.7
                    }}>
                        {viewingFile.one_time_view
                            ? "⚠️ Bu içerik korumalıdır. Ekran görüntüsü alınamaz."
                            : "Bu içerik korumasızdır."}
                    </div>
                </div>
            </div>
        );
    };

    // Depolama alanı yüzdesini hesapla
    const maxStorage = 10 * 1024 * 1024 * 1024;
    const storagePercentage = Math.min((totalStorage / maxStorage) * 100, 100);
    const usedGB = (totalStorage / (1024 * 1024 * 1024)).toFixed(2);
    const remainingGB = (10 - usedGB).toFixed(2);
    const memoryPercentage = Math.min((memoryUsage / 10) * 100, 100);
    const remainingMemory = 10 - memoryUsage;

    // Debug için: Tüm dosya bilgilerini konsola yazdır
    useEffect(() => {
        if (files.length > 0) {
            console.log('📁 Tüm Dosya Bilgileri:', files);
            files.forEach((file, index) => {
                console.log(`📄 Dosya ${index + 1}:`, {
                    id: file.id,
                    name: file.file_name,
                    file_field: file.file,
                    file_url: file.file_url,
                    preview_url: getFilePreview(file),
                    full_data: file
                });
            });
        }
    }, [files]);

    return (
        <div className="chunk-downloader">
            <div className="cloud-header">
                <h2>
                    <i className="fas fa-cloud-upload-alt"></i>
                    Bulutum - Dosya Yöneticisi
                </h2>
                <p>Dosyalarınızı yükleyin ve yönetin</p>
            </div>

            {/* Depolama ve Hafıza Görselleştirme */}
            <div className="storage-visualization">
                <StoragePieChart
                    percentage={storagePercentage}
                    used={usedGB}
                    remaining={remainingGB}
                />

                <BrainMemoryVisualization
                    percentage={memoryPercentage}
                    used={memoryUsage}
                    remaining={remainingMemory}
                />
            </div>

            {/* Dosya Yükleme Formu */}
            <div className="upload-section">
                <h3>📁 Dosya Yükle</h3>
                <form onSubmit={handleFileUpload} className="upload-form">
                    <div className="file-input-group">
                        <label className="file-input-label">
                            <input
                                id="file-input"
                                type="file"
                                onChange={(e) => setSelectedFile(e.target.files[0])}
                                disabled={uploading}
                            />
                            <div className="file-input-custom">
                                <i className="fas fa-cloud-upload-alt"></i>
                                {selectedFile ? selectedFile.name : "Dosya Seç..."}
                            </div>
                        </label>
                    </div>

                    {/* Görünüm Seçenekleri */}
                    <div className="upload-option-group">
                        <label className="option-label">👁️ Görünüm</label>
                        <div className="option-buttons">
                            <button
                                type="button"
                                className={`option-button ${viewOption === 'standard' ? 'active' : ''}`}
                                onClick={() => setViewOption('standard')}
                            >
                                Standart
                            </button>
                            <button
                                type="button"
                                className={`option-button ${viewOption === 'one_time' ? 'active' : ''}`}
                                onClick={() => setViewOption('one_time')}
                            >
                                Tek Seferlik
                            </button>
                        </div>
                        <div className="option-description">
                            {viewOption === 'one_time'
                                ? "Dosya sadece bir kez görüntülenebilir"
                                : "Dosya standart şekilde paylaşılır"
                            }
                        </div>

                        {/* Görüntüleme Süresi Seçenekleri - Sadece Tek Seferlik seçildiğinde görünecek */}
                        {viewOption === 'one_time' && (
                            <div className="upload-option-group">
                                <label className="option-label">⏱️ Görüntüleme Süresi</label>
                                <div className="duration-options">
                                    {viewDurationOptions.map(option => (
                                        <div
                                            key={option.value}
                                            className={`duration-option ${viewDuration === option.value ? 'active' : ''}`}
                                            onClick={() => setViewDuration(option.value)}
                                        >
                                            <div className="duration-radio">
                                                <div className="radio-dot"></div>
                                            </div>
                                            <div className="duration-info">
                                                <div className="duration-label">{option.label}</div>
                                                <div className="duration-description">{option.description}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Gizlilik Seçenekleri */}
                    <div className="upload-option-group">
                        <label className="option-label">🔒 Gizlilik</label>
                        <div className="option-buttons">
                            <button
                                type="button"
                                className={`option-button ${privacyOption === 'public' ? 'active' : ''}`}
                                onClick={() => setPrivacyOption('public')}
                            >
                                Herkese Açık
                            </button>
                            <button
                                type="button"
                                className={`option-button ${privacyOption === 'private' ? 'active' : ''}`}
                                onClick={() => setPrivacyOption('private')}
                            >
                                Gizli
                            </button>
                        </div>
                    </div>

                    {/* Bölüm Ayırıcı */}
                    <hr className="section-divider" />

                    <button
                        type="submit"
                        disabled={uploading || !selectedFile}
                        className={`upload-button ${uploading ? 'uploading' : ''}`}
                    >
                        {uploading ? (
                            <>
                                <i className="fas fa-spinner fa-spin"></i>
                                Yükleniyor...
                            </>
                        ) : (
                            <>
                                <i className="fas fa-upload"></i>
                                Dosya Yükle
                            </>
                        )}
                    </button>
                </form>
            </div>

            {/* Dosya Listesi */}
            <div className="files-section">
                <div className="section-header">
                    <h3>📂 Dosyalarım</h3>
                    <span className="file-count">({files.length} dosya)</span>
                </div>

                {files.length === 0 ? (
                    <div className="no-files">
                        <i className="fas fa-folder-open"></i>
                        <p>Henüz dosya yüklenmemiş</p>
                        <small>Yukarıdaki formdan ilk dosyanızı yükleyebilirsiniz</small>
                    </div>
                ) : (
                    <div className="files-grid">
                            {files.map((file) => {
                                const previewUrl = getFilePreview(file);
                                const fileSizeMB = file.file_size ? (file.file_size / (1024 * 1024)).toFixed(2) : 'N/A';
                                const fileName = file.file_name || (file.file ? file.file.split('/').pop() : 'Dosya');

                                return (
                                    // ✅ DÜZELTME: JSX syntax hatası giderildi
                                    file.one_time_view ? (
                                        <SecureViewer key={file.id} file={file}>
                                            <div
                                                className="file-card"
                                                onClick={() => handleViewFile(file)}
                                            >
                                                <div className="file-preview">
                                                    {previewUrl ? (
                                                        <>
                                                            <img
                                                                src={previewUrl}
                                                                alt="Önizleme"
                                                                className="file-thumbnail"
                                                                onLoad={(e) => {
                                                                    console.log('✅ Thumbnail başarıyla yüklendi:', e.target.src);
                                                                    const icon = e.target.nextElementSibling;
                                                                    if (icon) {
                                                                        icon.style.display = 'none';
                                                                    }
                                                                }}
                                                            />
                                                        </>
                                                    ) : null}
                                                    <div
                                                        className={`file-icon ${previewUrl ? 'fallback' : ''}`}
                                                        style={{ display: previewUrl ? 'none' : 'flex' }}
                                                    >
                                                        <i className={getFileIcon(file)}></i>
                                                    </div>
                                                    {file.one_time_view && (
                                                        <div className="one-time-badge">
                                                            <i className="fas fa-lock"></i>
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="file-info">
                                                    <div className="file-name" title={fileName}>
                                                        {fileName}
                                                    </div>
                                                    <div className="file-meta">
                                                        <span className="file-date">
                                                            {new Date(file.uploaded_at).toLocaleDateString('tr-TR')}
                                                        </span>
                                                        <span className="file-size">
                                                            {fileSizeMB} MB
                                                        </span>
                                                    </div>
                                                    <div className="file-tags">
                                                        {file.one_time_view && (
                                                            <span className="tag tag-warning">
                                                                <i className="fas fa-eye"></i> Tek Seferlik
                                                            </span>
                                                        )}
                                                        {file.is_public ? (
                                                            <span className="tag tag-success">
                                                                <i className="fas fa-users"></i> Herkese Açık
                                                            </span>
                                                        ) : (
                                                            <span className="tag tag-private">
                                                                <i className="fas fa-lock"></i> Gizli
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="file-actions compact">
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDownloadFile(file);
                                                        }}
                                                        className="btn btn-primary btn-small"
                                                        title="Dosyayı indir"
                                                    >
                                                        <i className="fas fa-download"></i>
                                                    </button>
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleShareClick(file);
                                                        }}
                                                        className="btn btn-share btn-small"
                                                        title="Dosyayı paylaş"
                                                    >
                                                        <i className="fas fa-share-alt"></i>
                                                    </button>
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDeleteFile(file.id);
                                                        }}
                                                        className="btn btn-danger btn-small"
                                                        title="Dosyayı sil"
                                                    >
                                                        <i className="fas fa-trash"></i>
                                                    </button>
                                                </div>
                                            </div>
                                        </SecureViewer>
                                    ) : (
                                        // ✅ Normal dosyalar için SecureViewer kullanma
                                        <div
                                            key={file.id}
                                            className="file-card"
                                            onClick={() => handleViewFile(file)}
                                        >
                                            <div className="file-preview">
                                                {previewUrl ? (
                                                    <>
                                                        <img
                                                            src={previewUrl}
                                                            alt="Önizleme"
                                                            className="file-thumbnail"
                                                            onLoad={(e) => {
                                                                console.log('✅ Thumbnail başarıyla yüklendi:', e.target.src);
                                                                const icon = e.target.nextElementSibling;
                                                                if (icon) {
                                                                    icon.style.display = 'none';
                                                                }
                                                            }}
                                                        />
                                                    </>
                                                ) : null}
                                                <div
                                                    className={`file-icon ${previewUrl ? 'fallback' : ''}`}
                                                    style={{ display: previewUrl ? 'none' : 'flex' }}
                                                >
                                                    <i className={getFileIcon(file)}></i>
                                                </div>
                                                {file.one_time_view && (
                                                    <div className="one-time-badge">
                                                        <i className="fas fa-lock"></i>
                                                    </div>
                                                )}
                                            </div>
                                            <div className="file-info">
                                                <div className="file-name" title={fileName}>
                                                    {fileName}
                                                </div>
                                                <div className="file-meta">
                                                    <span className="file-date">
                                                        {new Date(file.uploaded_at).toLocaleDateString('tr-TR')}
                                                    </span>
                                                    <span className="file-size">
                                                        {fileSizeMB} MB
                                                    </span>
                                                </div>
                                                <div className="file-tags">
                                                    {file.one_time_view && (
                                                        <span className="tag tag-warning">
                                                            <i className="fas fa-eye"></i> Tek Seferlik
                                                        </span>
                                                    )}
                                                    {file.is_public ? (
                                                        <span className="tag tag-success">
                                                            <i className="fas fa-users"></i> Herkese Açık
                                                        </span>
                                                    ) : (
                                                        <span className="tag tag-private">
                                                            <i className="fas fa-lock"></i> Gizli
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="file-actions compact">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDownloadFile(file);
                                                    }}
                                                    className="btn btn-primary btn-small"
                                                    title="Dosyayı indir"
                                                >
                                                    <i className="fas fa-download"></i>
                                                </button>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleShareClick(file);
                                                    }}
                                                    className="btn btn-share btn-small"
                                                    title="Dosyayı paylaş"
                                                >
                                                    <i className="fas fa-share-alt"></i>
                                                </button>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDeleteFile(file.id);
                                                    }}
                                                    className="btn btn-danger btn-small"
                                                    title="Dosyayı sil"
                                                >
                                                    <i className="fas fa-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    )
                                );
                            })}

                    </div>
                )}

                {/* Paylaşım Modal'ı */}
                {renderShareModal()}

                {/* Dosya Görüntüleyici Modal'ı */}
                {renderFileViewer()}
            </div>
        </div>
    );
};

export default ChunkDownloader;