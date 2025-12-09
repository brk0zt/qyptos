// Dashboard.jsx (Düzeltilmiş Versiyon)
import React, { useState, useEffect, useCallback, useRef } from "react";
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

const API_BASE = "http://localhost:8001"; // Resimler için Backend adresi

const MemoryStatsView = ({ stats }) => {
    if (!stats) return <div className="loading-state">Hafıza İstatistikleri yükleniyor...</div>;

    const {
        total_items,
        memory_quota_mb,
        memory_used_mb,
        memory_remaining_mb,
        tier_distribution
    } = stats;

    // Yüzde hesapla (Sıfıra bölünme hatasını engelle)
    const usedPercentage = memory_quota_mb > 0
        ? ((memory_used_mb / memory_quota_mb) * 100).toFixed(1)
        : "0.0";

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
        </div>
    );
};

const WelcomeChatSection = ({ username, onFileSelect, onRefreshTimeline }) => {
    const [inputText, setInputText] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [aiResponse, setAiResponse] = useState(null);
    const [foundMemories, setFoundMemories] = useState([]);
    const [suggestions, setSuggestions] = useState([]);

    const handleSendMessage = async (overrideText = null) => {
        const textToSend = overrideText || inputText;

        if (!textToSend.trim() || isProcessing) return;

        setIsProcessing(true);
        setAiResponse(null);
        setFoundMemories([]);
        setSuggestions([]); // Önceki önerileri temizle

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000);

        try {
            const token = localStorage.getItem('token');
            console.log("Sorgu:", textToSend);

            const response = await fetch(`${API_BASE}/api/chat/ask/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message: textToSend }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            const rawData = await response.json();
            // Backend bazen {data: ...} bazen direkt {...} dönebilir, ikisini de kapsayalım
            const data = rawData.data || rawData;

            console.log("📦 AI Yanıtı:", data);

            if (response.ok) {
                // 1. Cevap Metni
                setAiResponse(data.reply || "Sonuç bulundu.");

                // 2. Öneriler (Şaibe Varsa)
                if (data.suggestions && data.suggestions.length > 0) {
                    console.log("💡 Öneriler geldi:", data.suggestions);
                    setSuggestions(data.suggestions);
                }

                // 3. Hafıza Kartları (Resimler)
                const memories = data.relevant_memories || [];
                if (memories.length > 0) {
                    setFoundMemories(memories);
                }

                if (onRefreshTimeline) onRefreshTimeline();
            } else {
                setAiResponse("Hata: " + (data.detail || "İşlem başarısız."));
            }

        } catch (error) {
            console.error("Frontend Hatası:", error);
            setAiResponse(error.name === 'AbortError' ? "Zaman aşımı." : "Bağlantı hatası.");
        } finally {
            setIsProcessing(false);
            if (!overrideText) setInputText(""); // Sadece inputtan geldiyse temizle
            clearTimeout(timeoutId);
        }
    };

    return (
        <div className="welcome-chat-wrapper">
            <div className="welcome-header">
                <img src="/logo-tri.png" alt="Qyptos AI" className="welcome-logo-img" />
                <h1>Merhaba {username || 'Kullanıcı'}</h1>
            </div>

            <div className="gemini-input-container">
                <input
                    type="text"
                    placeholder="Qyptos AI'a sorun"
                    className="gemini-text-input"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                    disabled={isProcessing}
                />
                <button className="gemini-icon-btn mic-btn" onClick={() => handleSendMessage()}>
                    <i className={`fas ${isProcessing ? 'fa-spinner fa-spin' : 'fa-paper-plane'}`}></i>
                </button>
            </div>

            {/* SONUÇ ALANI */}
            <div className="ai-result-area" style={{ marginTop: '20px', padding: '10px' }}>

                {/* 1. Yapay Zeka Cevabı */}
                {aiResponse && (
                    <div className="ai-text-bubble" style={{ color: 'white', marginBottom: '15px' }}>
                        <i className="fas fa-robot"></i> {aiResponse}
                    </div>
                )}

                {/* 2. ÖNERİ BUTONLARI (Chips) - YENİ ÖZELLİK */}
                {suggestions.length > 0 && (
                    <div className="suggestions-container" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '20px' }}>
                        {suggestions.map((sug, index) => (
                            <button
                                key={index}
                                onClick={() => handleSendMessage(sug.search_query)}
                                style={{
                                    padding: '10px 20px',
                                    borderRadius: '20px',
                                    border: '1px solid #3B82F6',
                                    background: 'rgba(59, 130, 246, 0.1)',
                                    color: '#3B82F6',
                                    cursor: 'pointer',
                                    fontSize: '0.9rem',
                                    transition: 'all 0.2s',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px'
                                }}
                                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(59, 130, 246, 0.3)'}
                                onMouseOut={(e) => e.currentTarget.style.background = 'rgba(59, 130, 246, 0.1)'}
                            >
                                {sug.label}
                            </button>
                        ))}
                    </div>
                )}

                {/* 3. Bulunan Dosyalar */}
                {foundMemories.length > 0 && (
                    <div style={{ borderTop: '1px solid #333', paddingTop: '10px' }}>
                        <small style={{ color: '#666' }}>Bulunan Dosyalar ({foundMemories.length}):</small>
                        {foundMemories.map((mem, index) => (
                            <MemoryResultCard key={index} memory={mem} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

// Dashboard.jsx içindeki MemoryResultCard bileşeni (Güncellenmiş)

const MemoryResultCard = ({ memory }) => {
    // URL Kontrolü
    let imageUrl = memory.thumbnail || '';
    if (imageUrl && !imageUrl.startsWith('http')) {
        const cleanBase = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE;
        const cleanPath = imageUrl.startsWith('/') ? imageUrl : `/${imageUrl}`;
        imageUrl = `${cleanBase}${cleanPath}`;
    }

    // Dosya türü
    const isImage = memory.file_type === 'image' ||
        memory.file_name?.match(/\.(jpg|jpeg|png|gif|bmp|webp)$/i);

    // Video zaman bilgisi içeriyor mu?
    const hasTimestamp = memory.summary && memory.summary.includes('saniyesinde');

    return (
        <div className="memory-result-card"
            onClick={() => window.open(imageUrl, '_blank')}
            style={{
                background: '#1a1a1a',
                border: hasTimestamp ? '1px solid #FBBF24' : '1px solid #3B82F6', // Video bulunursa Sarı çerçeve
                borderRadius: '12px',
                padding: '15px',
                marginTop: '15px',
                display: 'flex',
                gap: '15px',
                cursor: 'pointer',
                minHeight: '80px',
                color: 'white'
            }}
        >
            {/* Küçük Resim */}
            <div style={{
                width: '80px', height: '80px',
                borderRadius: '8px', overflow: 'hidden',
                background: '#000', flexShrink: 0,
                border: '1px solid rgba(255,255,255,0.1)',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
                {isImage && imageUrl ? (
                    <img src={imageUrl} alt="thumbnail" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        onError={(e) => { e.target.style.display = 'none'; }} />
                ) : (
                    <div style={{ fontSize: '2rem', color: '#fff' }}>
                        <i className={memory.file_type === 'video' ? "fas fa-video" : "fas fa-file-alt"}></i>
                    </div>
                )}
            </div>

            {/* Bilgi Alanı */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <h4 style={{ margin: '0 0 5px 0', color: hasTimestamp ? '#FBBF24' : '#3B82F6', fontSize: '1rem' }}>
                    {memory.file_name}
                </h4>

                {/* Özet / Zaman Damgası Alanı - GÖRÜNÜR YAPILDI */}
                <p style={{
                    margin: '0 0 5px 0',
                    fontSize: '0.9rem',
                    color: hasTimestamp ? '#FBBF24' : '#ccc', // Sarı veya Açık Gri
                    fontWeight: hasTimestamp ? 'bold' : 'normal'
                }}>
                    {memory.summary || "Görsel içerik."}
                </p>

                <div style={{ fontSize: '0.75rem', opacity: 0.6, color: '#aaa' }}>
                    <i className="fas fa-bullseye" style={{ marginRight: '5px' }}></i>
                    Skor: %{(memory.similarity_score * 100).toFixed(0)}
                </div>
            </div>
        </div>
    );
};

const ChronologyBar = ({ refreshTrigger }) => {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchTimeline = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE}/api/timeline/?days=7&limit=10`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();

            if (data.timeline_events) {
                setEvents(data.timeline_events);
            }
        } catch (error) {
            console.error("Timeline hatası:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTimeline();
    }, [refreshTrigger]);

    if (loading) return <div className="chronology-wrapper" style={{ padding: '20px', textAlign: 'center' }}>Yükleniyor...</div>;

    return (
        <div className="chronology-wrapper">
            <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '15px' }}>Son Aktiviteler</h3>
            <div className="chronology-track" style={{ overflowX: 'auto', paddingBottom: '10px', display: 'flex', gap: '20px' }}>
                {events.length === 0 ? (
                    <div style={{ color: 'var(--text-muted)' }}>Henüz bir aktivite yok.</div>
                ) : (
                    events.map((event, index) => (
                        <div key={index} className="chrono-item" title={event.description} style={{ minWidth: '100px', textAlign: 'center' }}>
                            <div className={`chrono-dot ${index === 0 ? 'active' : ''}`} style={{ margin: '0 auto 10px auto' }}></div>
                            <span style={{ fontSize: '0.8rem', display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100px' }}>
                                {/* Uzun başlıkları kısalt */}
                                {event.title.length > 15 ? event.title.substring(0, 12) + '..' : event.title}
                            </span>
                            <small style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </small>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default function Dashboard({ notifications = [] }) {
    const { user, logout } = useAuth();
    const { fetchMemoryStats: fetchMemoryStatsFromContext } = useMemory();
    const [memoryStats, setMemoryStats] = useState(null);
    const [storageStats, setStorageStats] = useState({ used: 0, total: 50 });
    const [timelineRefresh, setTimelineRefresh] = useState(0);
    const [activeTab, setActiveTab] = useState("downloader");
    const [notificationCount] = useState(notifications.length || 3);
    const [selectedThread, setSelectedThread] = useState(null);
    const [onlineUsers, setOnlineUsers] = useState([]);
    const [theme, setTheme] = useState('dark');
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const dropdownRef = useRef(null);
    const [isThemeAnimating, setIsThemeAnimating] = useState(false);

    const handleTimelineRefresh = () => {
        setTimelineRefresh(prev => prev + 1);
    };

    const fetchStorageData = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) return;

            const response = await fetch(`${API_BASE}/api/files/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const files = await response.json();
                let totalBytes = 0;
                files.forEach(file => {
                    if (file.file_size) totalBytes += file.file_size;
                    else totalBytes += 1024 * 1024;
                });
                const usedGB = totalBytes / (1024 * 1024 * 1024);
                setStorageStats({ used: usedGB, total: 50 });
            }
        } catch (error) {
            console.error("Depolama verisi çekilemedi:", error);
        }
    };

    useEffect(() => {
        function handleClickOutside(event) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsDropdownOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [dropdownRef]);

    const fetchMemoryStats = useCallback(async () => {
        try {
            if (fetchMemoryStatsFromContext) {
                const stats = await fetchMemoryStatsFromContext();
                setMemoryStats(stats);
            } else {
                setMemoryStats({
                    memory_used_mb: 2.5,
                    memory_quota_mb: 100,
                    total_items: 42
                });
            }
        } catch (error) {
            console.error('Hata:', error);
            setMemoryStats({ memory_used_mb: 0, memory_quota_mb: 100 });
        }
    }, [fetchMemoryStatsFromContext]);

    useEffect(() => {
        fetchMemoryStats();
        fetchStorageData();
        const interval = setInterval(() => {
            fetchStorageData();
            fetchMemoryStats();
        }, 30000);
        return () => clearInterval(interval);
    }, [fetchMemoryStats]);

    const handleLogout = () => { logout(); };

    const toggleTheme = () => {
        setIsThemeAnimating(true);
        setTimeout(() => {
            const newTheme = theme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
            document.documentElement.setAttribute('data-theme', newTheme);
        }, 200);
        setTimeout(() => { setIsThemeAnimating(false); }, 500);
    };

    const toggleDropdown = () => { setIsDropdownOpen(!isDropdownOpen); };

    const onChatFileSelect = (file) => {
        alert(`"${file.name}" seçildi.`);
        setActiveTab("downloader");
    };

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        fetchMemoryStats();

        const fetchOnlineUsers = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) return;
                const response = await fetch(`${API_BASE}/chat/users/`, {
                    method: 'GET',
                    headers: { 'Authorization': `Bearer ${token}` },
                });
                if (response.ok) {
                    const users = await response.json();
                    setOnlineUsers(users);
                }
            } catch (error) {
                console.error('Kullanıcı listesi hatası:', error);
            }
        };
        fetchOnlineUsers();
    }, [logout, theme, fetchMemoryStats]);

    const renderContent = () => {
        switch (activeTab) {
            case "downloader":
                const storagePercent = Math.min((storageStats.used / storageStats.total) * 100, 100).toFixed(1);

                // NaN hatası düzeltmesi
                const memoryPercent = (memoryStats && memoryStats.memory_quota_mb > 0)
                    ? ((memoryStats.memory_used_mb / memoryStats.memory_quota_mb) * 100).toFixed(1)
                    : "0.0";

                return (
                    <div className="dashboard-home-layout">
                        <WelcomeChatSection
                            username={user?.username}
                            onFileSelect={onChatFileSelect}
                            onRefreshTimeline={handleTimelineRefresh}
                        />

                        <ChronologyBar refreshTrigger={timelineRefresh} />

                        <div className="stats-grid-visual">
                            <div className="qyptos-card storage-card">
                                <div className="card-header">
                                    <i className="fas fa-archive"></i>
                                    <h3>Depolama Alanı</h3>
                                </div>
                                <div className="circle-chart-wrapper">
                                    <svg viewBox="0 0 36 36" className="circular-chart blue">
                                        <path className="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                        <path className="circle" strokeDasharray={`${storagePercent}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                        <text x="18" y="20.35" className="percentage">{storagePercent}%</text>
                                    </svg>
                                </div>
                                <div className="card-footer">
                                    <span>Kullanılan: {storageStats.used.toFixed(2)} GB</span>
                                    <span>Toplam: {storageStats.total} GB</span>
                                </div>
                            </div>

                            <div className="qyptos-card memory-card">
                                <div className="card-header">
                                    <i className="fas fa-brain"></i>
                                    <h3>Yapay Hafıza</h3>
                                </div>
                                <div className="circle-chart-wrapper">
                                    <svg viewBox="0 0 36 36" className="circular-chart purple">
                                        <path className="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                        <path className="circle" strokeDasharray={`${memoryPercent}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                        <text x="18" y="20.35" className="percentage">{memoryPercent}%</text>
                                    </svg>
                                </div>
                                <div className="card-footer">
                                    <span>{memoryStats?.total_items || 0} Öğrenilen Bilgi</span>
                                </div>
                            </div>
                        </div>

                        <div className="downloader-container-wrapper">
                            <ChunkDownloader apiBase={`${API_BASE}/api`} />
                        </div>
                    </div>
                );
            case "groups": return <GroupManager />;
            case "memory": return <MemoryStatsView stats={memoryStats} />;
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
                                    <ChatHeader username={selectedThread.username} isOnline={selectedThread.isOnline} />
                                    <ChatBox threadId={selectedThread.id} currentUser={user?.username} />
                                </>
                            ) : (
                                <div className="no-chat-selected">
                                    <div className="no-chat-icon">💬</div>
                                    <h3>Bir sohbet başlatın</h3>
                                </div>
                            )}
                        </div>
                    </div>
                );
            case "ads": return <TrendingView />;
            case "media": return <SearchEngine />;
            case "profile":
                return (
                    <div className="content-placeholder">
                        <h2>Profil</h2>
                        <p>Kullanıcı: {user?.username}</p>
                    </div>
                );
            default: return <div>Seçim yapın</div>;
        }
    };

    return (
        <div className="dashboard-horizontal">
            <nav className="top-nav">
                <div className="nav-left">
                    <div className="logo">
                        <img src="/qyptos-logo.png" alt="qyptos-logo" className="qyptos-logo-img" />
                    </div>
                    <div className="nav-menu">
                        <div className={`nav-item ${activeTab === "downloader" ? "active" : ""}`} onClick={() => setActiveTab("downloader")}><i className="fas fa-cloud"></i> <span>Bulutum</span></div>
                        <div className={`nav-item ${activeTab === "ads" ? "active" : ""}`} onClick={() => setActiveTab("ads")}><i className="fas fa-fire"></i> <span>Trendler</span></div>
                        <div className={`nav-item ${activeTab === "media" ? "active" : ""}`} onClick={() => setActiveTab("media")}><i className="fas fa-search"></i> <span>Ara</span></div>
                        <div className={`nav-item ${activeTab === "groups" ? "active" : ""}`} onClick={() => setActiveTab("groups")}><i className="fas fa-users"></i> <span>Gruplar</span></div>
                        <div className={`nav-item ${activeTab === "chat" ? "active" : ""}`} onClick={() => setActiveTab("chat")}><i className="fas fa-comments"></i> <span>DM</span></div>
                    </div>
                </div>

                <div className="nav-right">
                    <div className={`theme-toggle ${isThemeAnimating ? 'animating' : ''}`} onClick={toggleTheme}>
                        <i className={`fas ${theme === 'dark' ? 'fa-moon' : 'fa-sun'}`}></i>
                    </div>
                    <div className="notification-bell">
                        <i className="fas fa-bell"></i>
                        {notificationCount > 0 && <span className="notification-badge">{notificationCount}</span>}
                    </div>
                    <div className="user-dropdown" onClick={toggleDropdown} ref={dropdownRef}>
                        <div className="user-avatar"><i className="fas fa-user"></i></div>
                        <span className="user-name">{user?.username || 'burak'}</span>
                        <i className={`fas fa-chevron-down ${isDropdownOpen ? 'rotate' : ''}`}></i>
                        {isDropdownOpen && (
                            <div className="dropdown-menu show">
                                <div className="dropdown-item" onClick={(e) => { e.stopPropagation(); setActiveTab("profile"); setIsDropdownOpen(false); }}><i className="fas fa-user"></i><span>Profil</span></div>
                                <div className="dropdown-item danger" onClick={(e) => { e.stopPropagation(); handleLogout(); }}><i className="fas fa-sign-out-alt"></i><span>Çıkış Yap</span></div>
                            </div>
                        )}
                    </div>
                </div>
            </nav>
            <main className="main-content-horizontal">
                {renderContent()}
            </main>
        </div>
    );
}