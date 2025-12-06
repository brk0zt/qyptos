import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../AuthContext";
import { useMemory } from "./MemoryContext";
import ChunkDownloader from "./ChunkDownloader";
import GroupManager from './GroupManager';
import ChatBox from "./ChatBox";
import ChatHeader from "./ChatHeader";
import UserList from "./UserList";
import TrendingView from './TrendingView';
import "./styles/Dashboard.css";
import SearchEngine from './SearchEngine';

const MemoryStatsView = ({ stats }) => {
    if (!stats) return <div className="loading-state">Hafıza İstatistikleri yükleniyor...</div>;

    const {
        total_items,
        memory_quota_mb,
        memory_used_mb,
        memory_remaining_mb,
        tier_distribution
    } = stats;

    // Yüzde hesapla
    const usedPercentage = ((memory_used_mb / memory_quota_mb) * 100).toFixed(1);

    return (
        <div className="memory-stats-view">
            <h2>🧠 Yapay Hafıza Durumu</h2>

            <div className="stat-card quota-card">
                <h3>Kullanım ve Kota</h3>
                <div className="progress-bar-container">
                    <div
                        className="progress-bar"
                        style={{ width: `${usedPercentage}%` }}
                    >
                        {usedPercentage}%
                    </div>
                </div>
                <p>Toplam Kullanılan: <strong>{memory_used_mb.toFixed(2)} MB</strong> / {memory_quota_mb.toFixed(2)} MB</p>
                <p>Kalan Kota: <strong>{memory_remaining_mb.toFixed(2)} MB</strong></p>
                <p>Toplam Kayıtlı Öğe: <strong>{total_items}</strong></p>
            </div>

            <div className="stat-card tier-card">
                <h3>Katman Dağılımı (Memory Tier)</h3>
                <ul className="tier-list">
                    {tier_distribution.map((tier, index) => (
                        <li key={index}>
                            <span className={`tier-name tier-${tier.memory_tier__name.replace('_', '-')}`}>
                                {tier.memory_tier__name.toUpperCase()}
                            </span>
                            <span className="tier-count">{tier.count} Öğe</span>
                        </li>
                    ))}
                </ul>
            </div>

            {/* ... Diğer detaylar eklenebilir (Örn: En çok erişilen öğeler, öğrenme hızı) ... */}
        </div>
    );
};

export default function Dashboard({ notifications = [] }) {
    const { user, logout } = useAuth();
    const { fetchMemoryStats: fetchMemoryStatsFromContext } = useMemory(); // MemoryContext'ten fonksiyonu al
    const [memoryStats, setMemoryStats] = useState(null);
    const [activeTab, setActiveTab] = useState("downloader");
    const [notificationCount] = useState(notifications.length || 3);
    const [selectedThread, setSelectedThread] = useState(null);
    const [onlineUsers, setOnlineUsers] = useState([]);
    const [theme, setTheme] = useState('dark');

    // fetchMemoryStats fonksiyonunu tanımla
    const fetchMemoryStats = useCallback(async () => {
        try {
            console.log('📊 Memory istatistikleri çekiliyor...');
            if (fetchMemoryStatsFromContext) {
                const stats = await fetchMemoryStatsFromContext();
                setMemoryStats(stats);
                return stats;
            } else {
                // Fallback: Direk API çağrısı
                const token = localStorage.getItem('token');
                const response = await fetch('http://localhost:8001/api/memory/stats/', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    }
                });

                if (response.ok) {
                    const stats = await response.json();
                    setMemoryStats(stats);
                    return stats;
                } else {
                    console.error('Memory stats alınamadı');
                    // Fallback stats
                    const fallbackStats = {
                        used_memory: 2.5,
                        total_memory: 10,
                        total_items: 25,
                        total_activities: 150,
                        file_type_count: 8
                    };
                    setMemoryStats(fallbackStats);
                    return fallbackStats;
                }
            }
        } catch (error) {
            console.error('❌ Memory istatistikleri yüklenirken hata:', error);
            // Fallback stats
            const fallbackStats = {
                used_memory: 2.5,
                total_memory: 10,
                total_items: 25,
                total_activities: 150,
                file_type_count: 8
            };
            setMemoryStats(fallbackStats);
            return fallbackStats;
        }
    }, [fetchMemoryStatsFromContext]);

    const handleLogout = () => {
        console.log('🚪 Dashboard logout butonuna tıklandı');
        logout();
    };

    const toggleTheme = () => {
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);
    };

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);

        // Memory istatistiklerini yükle
        fetchMemoryStats();

        const fetchOnlineUsers = async () => {
            try {
                const token = localStorage.getItem('token');
                console.log('🔑 Dashboard - Token kontrolü:', token ? '✅ VAR' : '❌ YOK');

                if (!token) {
                    console.error('❌ Token bulunamadı! Login sayfasına yönlendiriliyor...');
                    logout();
                    return;
                }

                console.log('🔄 Kullanıcı listesi çekiliyor...');
                const response = await fetch('http://localhost:8001/chat/users/', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                console.log('📡 Kullanıcı listesi response status:', response.status);

                if (response.status === 401) {
                    console.error('❌ Token geçersiz veya süresi dolmuş');
                    logout();
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const users = await response.json();
                console.log(`✅ ${users.length} kullanıcı yüklendi`);
                setOnlineUsers(users);

            } catch (error) {
                console.error('❌ Kullanıcı listesi yüklenirken hata:', error);
                setOnlineUsers([]);
            }
        };

        fetchOnlineUsers();
    }, [logout, theme, fetchMemoryStats]); // fetchMemoryStats'ı dependency array'e ekle

    const renderContent = () => {
        switch (activeTab) {
            case "downloader":
                return (
                    <div className="storage-memory-container">
                        <ChunkDownloader
                            apiBase="http://localhost:8001/api"
                            userEmail={user?.email}
                            theme={theme}
                            memoryStats={memoryStats}
                        />
                        <div className="memory-stats-placeholder" style={{
                            padding: '20px',
                            background: '#f5f5f5',
                            borderRadius: '8px',
                            textAlign: 'center',
                            color: '#666'
                        }}>
                            <h3>🧠 Hafıza İstatistikleri</h3>
                            <p>Hafıza modülü şu anda güncelleniyor...</p>
                        </div>
                    </div>
                );
            case "groups":
                return <GroupManager />;

            case "memory": 
                return <MemoryStatsView stats={memoryStats} />;

            case "chat":
                return (
                    <div className="chat-container">
                        <div className="chat-sidebar">
                            <UserList
                                users={onlineUsers}
                                currentUser={user?.username}
                                onSelectUser={(username) => {
                                    const selectedUser = onlineUsers.find(u => u.username === username);
                                    setSelectedThread({
                                        id: Date.now(),
                                        username: username,
                                        isOnline: selectedUser?.is_online || false
                                    });
                                }}
                            />
                        </div>
                        <div className="chat-main">
                            {selectedThread ? (
                                <>
                                    <ChatHeader
                                        username={selectedThread.username}
                                        isOnline={selectedThread.isOnline}
                                    />
                                    <ChatBox
                                        threadId={selectedThread.id}
                                        currentUser={user?.username}
                                    />
                                </>
                            ) : (
                                <div className="no-chat-selected">
                                    <div className="no-chat-icon">💬</div>
                                    <h3>Bir sohbet başlatın</h3>
                                    <p>Sohbet etmek için soldaki listeden bir kullanıcı seçin</p>
                                </div>
                            )}
                        </div>
                    </div>
                );
            case "ads":
                return <TrendingView />;

            case "media":
                return <SearchEngine />;

            case "profile":
                return (
                    <div className="content-placeholder">
                        <h2>Profil Ayarları</h2>
                        <p>Kullanıcı: {user?.username}</p>
                        <p>Email: {user?.email}</p>
                    </div>
                );
            default:
                return <div className="content-placeholder">Bir içerik seçin</div>;
        }
    };

    return (
        <div className="dashboard-horizontal">

            <nav className="sidebar-nav">
                <div className="nav-logo">
                    <i className="fas fa-brain"></i>
                    <span>Recall AI</span>
                </div>

                <div className="nav-links">
                    {/* YENİ Navigasyon Butonu */}
                    <div
                        className={`nav-link ${activeTab === 'memory' ? 'active' : ''}`}
                        onClick={() => setActiveTab('memory')}
                    >
                        <i className="fas fa-chart-bar"></i>
                        <span>Yapay Hafıza</span>
                    </div>

                    <div
                        className={`nav-link ${activeTab === 'timeline' ? 'active' : ''}`}
                        onClick={() => setActiveTab('timeline')}
                    >
                        <i className="fas fa-history"></i>
                        <span>Timeline (Recall)</span>
                    </div>
                    {/* ... Diğer nav-link'ler ... */}
                </div>
            </nav>

            {/* Üst Navigasyon Bar */}
            <nav className="top-nav">
                <div className="nav-left">
                    <div className="logo">
                        <img
                            src="/qyptos-logo.png"
                            alt="qyptos-logo"
                            className="qyptos-logo-img"
                        />
                    </div>

                    <div className="nav-menu">
                        <div
                            className={`nav-item ${activeTab === "downloader" ? "active" : ""}`}
                            onClick={() => setActiveTab("downloader")}
                        >
                            <i className="fas fa-cloud"></i>
                            <span>Bulutum</span>
                        </div>

                        <div
                            className={`nav-item ${activeTab === "ads" ? "active" : ""}`}
                            onClick={() => setActiveTab("ads")}
                        >
                            <i className="fas fa-fire"></i>
                            <span>Trendler</span>
                        </div>

                        <div
                            className={`nav-item ${activeTab === "media" ? "active" : ""}`}
                            onClick={() => setActiveTab("media")}
                        >
                            <i className="fas fa-search"></i>
                            <span>Ara</span>
                        </div>

                        <div
                            className={`nav-item ${activeTab === "groups" ? "active" : ""}`}
                            onClick={() => setActiveTab("groups")}
                        >
                            <i className="fas fa-users"></i>
                            <span>Gruplar</span>
                        </div>

                        <div
                            className={`nav-item ${activeTab === "chat" ? "active" : ""}`}
                            onClick={() => setActiveTab("chat")}
                        >
                            <i className="fas fa-comments"></i>
                            <span>DM</span>
                        </div>
                    </div>
                </div>

                <div className="nav-right">
                    {/* Tema Değiştirme Butonu */}
                    <div className="theme-toggle" onClick={toggleTheme}>
                        <i className={`fas ${theme === 'dark' ? 'fa-sun' : 'fa-moon'}`}></i>
                    </div>

                    <div className="notification-bell">
                        <i className="fas fa-bell"></i>
                        {notificationCount > 0 && (
                            <span className="notification-badge">{notificationCount}</span>
                        )}
                    </div>

                    <div className="user-dropdown">
                        <div className="user-avatar">
                            <i className="fas fa-user"></i>
                        </div>
                        <span className="user-name">{user?.username || 'Kullanıcı'}</span>
                        <i className="fas fa-chevron-down"></i>

                        <div className="dropdown-menu">
                            <div className="dropdown-item" onClick={() => setActiveTab("profile")}>
                                <i className="fas fa-user"></i>
                                <span>Profil</span>
                            </div>
                            <div className="dropdown-item">
                                <i className="fas fa-cog"></i>
                                <span>Ayarlar</span>
                            </div>
                            <div className="dropdown-divider"></div>
                            <div className="dropdown-item" onClick={handleLogout}>
                                <i className="fas fa-sign-out-alt"></i>
                                <span>Çıkış Yap</span>
                            </div>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Ana İçerik Alanı */}
            <main className="main-content-horizontal">
                {renderContent()}
            </main>
        </div>
    );
}