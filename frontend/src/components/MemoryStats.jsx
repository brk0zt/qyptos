import React, { useState, useEffect } from 'react';
import { useAuth } from "../AuthContext";
import './MemoryStats.css';

const MemoryStats = ({ user, compact = true }) => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const { logout } = useAuth();

    useEffect(() => {
        fetchMemoryStats();
    }, []);

    const fetchMemoryStats = async () => {
        try {
            const token = localStorage.getItem('token');
            console.log('🔐 Memory stats için token:', token ? 'Mevcut' : 'Yok');

            const response = await fetch('http://localhost:8001/api/memory/stats/', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            console.log('📊 Memory stats response:', response.status);

            if (response.status === 401) {
                console.error('❌ Yetkilendirme hatası - Token geçersiz');
                logout();
                return;
            }

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Memory stats başarılı:', data);
                setStats(data);
            } else {
                console.error('❌ Memory stats alınamadı:', response.status);
                setStats(getFallbackStats());
            }
        } catch (error) {
            console.error('❌ Memory stats yüklenirken hata:', error);
            setStats(getFallbackStats());
        } finally {
            setLoading(false);
        }
    };

    const getFallbackStats = () => {
        return {
            used_memory: 2.5,
            total_memory: 10,
            memory_percentage: 25,
            total_items: 25,
            total_activities: 150,
            file_type_count: 8,
            learning_rate: 0.1,
            last_activity: new Date().toISOString(),
            status: 'active',
            total_size_mb: 2560
        };
    };

    const BrainVisual = ({ percentage }) => {
        const fillHeight = Math.max(10, Math.min(100, percentage));

        return (
            <div className="brain-visual-container">
                <div className="brain-silhouette">
                    <div
                        className="brain-fill"
                        style={{ height: `${fillHeight}%` }}
                    ></div>
                    <div className="brain-outline">
                        <div className="brain-lobe left"></div>
                        <div className="brain-lobe right"></div>
                    </div>
                    <div className="brain-percentage">{percentage}%</div>
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className={`memory-stats ${compact ? 'compact-stats' : ''} loading`}>
                <div className="loading-spinner"></div>
                <p>Hafıza istatistikleri yükleniyor...</p>
            </div>
        );
    }

    if (!stats) {
        return (
            <div className={`memory-stats ${compact ? 'compact-stats' : ''} error`}>
                <p>Hafıza istatistikleri yüklenemedi</p>
                <button onClick={fetchMemoryStats} className="retry-btn">
                    Tekrar Dene
                </button>
            </div>
        );
    }

    // Sadece compact versiyonu kullanıyoruz
    return (
        <div className={`memory-stats ${compact ? 'compact-stats' : ''}`}>
            <div className="brain-header">
                <div className="brain-icon">🧠</div>
                <div>
                    <div className="brain-title">Yapay Hafıza</div>
                    <div className="brain-subtitle">Akıllı bellek yönetimi aktif</div>
                </div>
            </div>

            <div className="storage-visualization">
                <div className="brain-memory">
                    <BrainVisual percentage={stats.memory_percentage || 0} />
                    <div className="memory-info">
                        <div className="info-item">
                            <div className="info-value">{stats.used_memory || 0} GB</div>
                            <div className="info-label">Kullanılan</div>
                        </div>
                        <div className="info-item">
                            <div className="info-value">{stats.total_items || 0}</div>
                            <div className="info-label">Öğe</div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="memory-details-grid">
                <div className="detail-card">
                    <div className="detail-icon">📊</div>
                    <div className="detail-content">
                        <div className="detail-value">{stats.file_type_count || 0}</div>
                        <div className="detail-label">Dosya Türü</div>
                    </div>
                </div>

                <div className="detail-card">
                    <div className="detail-icon">⚡</div>
                    <div className="detail-content">
                        <div className="detail-value">%{(stats.learning_rate || 0.1) * 100}</div>
                        <div className="detail-label">Öğrenme</div>
                    </div>
                </div>

                <div className="detail-card">
                    <div className="detail-icon">💾</div>
                    <div className="detail-content">
                        <div className="detail-value">{stats.total_size_mb || 0} MB</div>
                        <div className="detail-label">Toplam Boyut</div>
                    </div>
                </div>

                <div className="detail-card">
                    <div className="detail-icon">📈</div>
                    <div className="detail-content">
                        <div className="detail-value">{stats.total_activities || 0}</div>
                        <div className="detail-label">Aktivite</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MemoryStats;