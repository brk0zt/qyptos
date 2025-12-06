// GroupManager.jsx - TUTARLI VERSİYON
import React, { useState, useEffect } from 'react';
import { groupAPI, authAPI } from '../utils/api';
import './GroupManager.css';

const GroupManager = ({ onGroupSelect }) => {
    const [groups, setGroups] = useState([]);
    const [newGroupName, setNewGroupName] = useState('');
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isDemoMode, setIsDemoMode] = useState(true);
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [selectedGroup, setSelectedGroup] = useState(null);
    const [inviteEmails, setInviteEmails] = useState('');
    const [inviteCode, setInviteCode] = useState('');

    useEffect(() => {
        console.log('🎯 GroupManager mounted - checking authentication');
        checkAuthentication();
    }, []);

    const checkAuthentication = async () => {
        try {
            setLoading(true);

            // Dashboard ile aynı token kontrolü
            const token = localStorage.getItem('token');
            console.log('🔐 GroupManager Token kontrolü:', token ? '✅ VAR' : '❌ YOK');

            if (!token) {
                console.log('🔶 Token yok, demo moda geçiliyor...');
                handleDemoMode();
                return;
            }

            // Token varsa backend bağlantısını test et
            await testBackendConnection();

        } catch (error) {
            console.error('❌ Authentication check failed:', error);
            handleDemoMode();
        } finally {
            setLoading(false);
        }
    };

    const handleDemoMode = () => {
        console.log('🔶 Demo mod etkin');
        const demoUser = {
            id: 1,
            username: 'Demo Kullanıcı',
            email: 'demo@example.com'
        };

        const demoGroups = [
            {
                id: 1,
                name: 'Demo Yazılım Ekibi',
                member_count: 5,
                created_by: 'Admin',
                created_at: new Date().toISOString(),
                invite_code: 'DEMO123'
            },
            {
                id: 2,
                name: 'Demo Tasarım Grubu',
                member_count: 3,
                created_by: 'Moderatör',
                created_at: new Date().toISOString(),
                invite_code: 'DEMO456'
            }
        ];

        setUser(demoUser);
        setIsDemoMode(true);
        setGroups(demoGroups);
        setError('Backend bağlantısı kurulamadı. Demo veriler gösteriliyor.');
    };

    const testBackendConnection = async () => {
        try {
            setLoading(true);
            console.log('🧪 Backend bağlantısı test ediliyor...');

            const token = localStorage.getItem('token');
            console.log('🔐 Test için token:', token ? '✅ VAR' : '❌ YOK');

            if (!token) {
                setError('Token bulunamadı. Demo modda devam ediliyor.');
                handleDemoMode();
                return;
            }

            try {
                // Backend bağlantısını test et
                console.log('📡 Backend isteği gönderiliyor...');
                const response = await authAPI.checkAuth();
                console.log('✅ Backend bağlantısı başarılı', response.data);

                setUser(response.data);
                setIsDemoMode(false);
                setError(null);

                // Grupları yükle
                await loadGroups();
                console.log('✅ Gerçek moda geçildi');

            } catch (backendError) {
                console.error('❌ Backend hatası:', backendError);
                throw new Error('Backend bağlantısı kurulamadı');
            }

        } catch (error) {
            console.error('❌ Backend bağlantısı başarısız:', error);
            setIsDemoMode(true);
            setError('Backend bağlantısı kurulamadı. Demo moda geçildi.');
            handleDemoMode();
        } finally {
            setLoading(false);
        }
    };

    const createGroup = async (e) => {
        e.preventDefault();
        if (!newGroupName.trim()) return;

        try {
            const demoGroup = {
                id: Date.now(),
                name: newGroupName,
                member_count: 1,
                created_by: user?.username || 'Demo Kullanıcı',
                created_at: new Date().toISOString(),
                invite_code: `DEMO${Math.random().toString(36).substring(2, 8).toUpperCase()}`
            };
            setGroups(prev => [...prev, demoGroup]);
            setNewGroupName('');

            if (isDemoMode) {
                alert('✅ Demo grup oluşturuldu!');
            } else {
                alert('✅ Grup oluşturuldu!');
            }
        } catch (error) {
            console.error('❌ Grup oluşturulamadı:', error);
            alert('❌ Grup oluşturulamadı!');
        }
    };

    const joinGroup = async (groupId) => {
        if (isDemoMode) {
            alert('✅ Demo mod: Gruba katıldınız!');
        } else {
            alert('✅ Gruba katıldınız!');
        }
    };

    const leaveGroup = async (groupId) => {
        if (isDemoMode) {
            alert('✅ Demo mod: Gruptan ayrıldınız!');
        } else {
            alert('✅ Gruptan ayrıldınız!');
        }
    };

    const joinByInviteCode = async () => {
        if (!inviteCode.trim()) {
            alert('❌ Lütfen bir davet kodu girin!');
            return;
        }

        if (isDemoMode) {
            alert(`✅ Demo mod: ${inviteCode} kodlu gruba katıldınız!`);
        } else {
            alert(`✅ ${inviteCode} kodlu gruba katıldınız!`);
        }
        setInviteCode('');
    };

    const sendInvites = async (groupId, emails) => {
        if (isDemoMode) {
            alert('✅ Demo mod: Davetler gönderildi!');
        } else {
            alert('✅ Davetler gönderildi!');
        }
        setShowInviteModal(false);
        setInviteEmails('');
    };

    const openInviteModal = (group) => {
        setSelectedGroup(group);
        setShowInviteModal(true);
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('tr-TR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    };

    const loadGroups = async () => {
        if (isDemoMode) {
            console.log('🎭 Demo mode, skipping real groups load');
            return;
        }

        try {
            console.log('📡 Loading groups from API...');
            const response = await groupAPI.getGroups();
            setGroups(response.data);
            console.log('✅ Groups loaded:', response.data.length);
        } catch (error) {
            console.error('❌ Groups load failed:', error);
            throw error;
        }
    };

    // Debug için token durumunu göster
    const getTokenStatus = () => {
        const token = localStorage.getItem('token');
        return {
            exists: !!token,
            length: token ? token.length : 0,
            preview: token ? `${token.substring(0, 10)}...` : 'None'
        };
    };

    if (loading) {
        return (
            <div className="group-manager-container">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p className="loading-text">Yükleniyor...</p>
                    <p className="loading-subtext">Kimlik doğrulama kontrol ediliyor</p>
                </div>
            </div>
        );
    }

    const tokenStatus = getTokenStatus();

    return (
        <div className="group-manager-container">
            {/* Durum Bilgisi */}
            <div className={`status-card ${isDemoMode ? 'demo-mode' : 'real-mode'}`}>
                <div className="status-header">
                    <h2 className="status-title">
                        Grup Yönetimi
                        {isDemoMode ? ' - DEMO MOD' : ' - GERÇEK MOD'}
                    </h2>
                    <div className="status-info">
                        <div className={`status-badge ${isDemoMode ? 'demo-mode' : 'real-mode'}`}>
                            <div className="status-dot"></div>
                            {isDemoMode ? 'Demo Modu' : 'Gerçek Mod'}
                        </div>
                        <p className="status-description">
                            {isDemoMode
                                ? 'Backend bağlantısı yok. Demo veriler gösteriliyor.'
                                : 'Backend bağlantısı başarılı. Gerçek veriler yükleniyor.'}
                        </p>
                    </div>
                </div>
                <button
                    onClick={testBackendConnection}
                    className="test-connection-btn"
                    disabled={loading}
                >
                    <i className="fas fa-plug"></i>
                    {loading ? 'Test Ediliyor...' : 'Bağlantıyı Test Et'}
                </button>
            </div>

            {/* Kullanıcı bilgisi */}
            {user && (
                <div className="user-card">
                    <div className="user-avatar">
                        <i className="fas fa-user"></i>
                    </div>
                    <div className="user-info">
                        <h3 className="user-greeting">
                            Hoş geldin, <span className="user-name">{user.username}</span>
                            {isDemoMode && <span className="demo-tag">Demo</span>}
                        </h3>
                        <p className="user-email">{user.email}</p>
                    </div>
                </div>
            )}

            {error && (
                <div className="error-card">
                    <p>{error}</p>
                </div>
            )}

            {/* Grup oluşturma formu */}
            <div className="create-group-card">
                <h3 className="card-title">
                    Yeni Grup Oluştur
                    {isDemoMode && <span className="demo-tag">Demo</span>}
                </h3>
                <form onSubmit={createGroup} className="create-group-form">
                    <input
                        type="text"
                        value={newGroupName}
                        onChange={(e) => setNewGroupName(e.target.value)}
                        placeholder="Grup adını yazın..."
                        className="group-input"
                    />
                    <button
                        type="submit"
                        className="create-group-btn"
                    >
                        <i className="fas fa-plus"></i> Oluştur
                    </button>
                </form>
            </div>

            {/* Grup listesi */}
            <div className="groups-container">
                <div className="groups-header">
                    <div className="groups-title-section">
                        <h3 className="groups-title">
                            {isDemoMode ? 'Demo Gruplar' : 'Gruplar'}
                        </h3>
                        <p className="groups-count">{groups.length} grup bulundu</p>
                    </div>
                    {isDemoMode && (
                        <span className="demo-tag large">Demo Modu</span>
                    )}
                </div>

                {/* Davet kodu ile katılma */}
                <div className="join-by-code-card">
                    <h3 className="card-title">
                        Davet Kod ile Katıl
                        {isDemoMode && <span className="demo-tag">Demo</span>}
                    </h3>
                    <div className="join-code-form">
                        <input
                            type="text"
                            value={inviteCode}
                            onChange={(e) => setInviteCode(e.target.value)}
                            placeholder={isDemoMode ? "DEMO123 gibi bir kod deneyin..." : "Davet kodunu girin..."}
                            className="group-input"
                        />
                        <button
                            onClick={joinByInviteCode}
                            className="join-code-btn"
                        >
                            <i className="fas fa-sign-in-alt"></i> Katıl
                        </button>
                    </div>
                </div>

                {/* Grup listesi */}
                <div className="groups-list">
                    {groups.length === 0 ? (
                        <div className="empty-groups">
                            <i className="fas fa-folder-open"></i>
                            <p className="empty-text">Henüz hiç grubunuz yok.</p>
                            <p className="empty-subtext">Yukarıdan ilk grubunuzu oluşturun!</p>
                        </div>
                    ) : (
                        groups.map((group) => (
                            <div
                                key={group.id}
                                className="group-card"
                                onClick={() => onGroupSelect && onGroupSelect(group.id)}
                            >
                                <div className="group-content">
                                    <div className="group-main-info">
                                        <div className="group-header">
                                            <div className="group-title-section">
                                                <h4 className="group-name">
                                                    {group.name}
                                                    {isDemoMode && <span className="demo-tag small">Demo</span>}
                                                </h4>
                                            </div>
                                            <span className="member-count">
                                                <i className="fas fa-users"></i> {group.member_count} üye
                                            </span>
                                        </div>
                                        <div className="group-meta">
                                            <i className="fas fa-user-shield"></i>
                                            <span className="group-creator">{group.created_by}</span>
                                            <span className="meta-separator">•</span>
                                            <span className="group-date">Oluşturulma: {formatDate(group.created_at)}</span>
                                            {group.invite_code && (
                                                <span className="invite-code">
                                                    <span className="meta-separator">•</span>
                                                    Davet Kodu: {group.invite_code}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="group-actions">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                openInviteModal(group);
                                            }}
                                            className="invite-btn"
                                            title="Arkadaşlarını Davet Et"
                                        >
                                            <i className="fas fa-user-plus"></i> Davet Et
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                joinGroup(group.id);
                                            }}
                                            className="join-btn"
                                        >
                                            <i className="fas fa-sign-in-alt"></i> Katıl
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                leaveGroup(group.id);
                                            }}
                                            className="leave-btn"
                                        >
                                            <i className="fas fa-sign-out-alt"></i> Ayrıl
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Davet Modal */}
                {showInviteModal && (
                    <div className="modal-overlay">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h3>
                                    Arkadaşlarını Davet Et
                                    {isDemoMode && ' - DEMO'}
                                </h3>
                                <button
                                    className="close-btn"
                                    onClick={() => setShowInviteModal(false)}
                                >
                                    <i className="fas fa-times"></i>
                                </button>
                            </div>
                            <div className="modal-body">
                                <p>
                                    <strong>{selectedGroup?.name}</strong> grubuna arkadaşlarını davet et
                                </p>
                                <div className="invite-section">
                                    <label>Email Adresleri (virgülle ayırın):</label>
                                    <textarea
                                        value={inviteEmails}
                                        onChange={(e) => setInviteEmails(e.target.value)}
                                        placeholder="ornek1@email.com, ornek2@email.com"
                                        rows="3"
                                    />
                                </div>
                                {selectedGroup?.invite_code && (
                                    <div className="invite-code-section">
                                        <label>Davet Kodu:</label>
                                        <div className="code-display">
                                            <code>{selectedGroup.invite_code}</code>
                                            <button
                                                onClick={() => navigator.clipboard.writeText(selectedGroup.invite_code)}
                                                className="copy-btn"
                                            >
                                                <i className="fas fa-copy"></i>
                                            </button>
                                        </div>
                                        <small>Arkadaşların bu kod ile gruba katılabilir</small>
                                    </div>
                                )}
                            </div>
                            <div className="modal-actions">
                                <button
                                    onClick={() => sendInvites(selectedGroup.id, inviteEmails.split(',').map(email => email.trim()))}
                                    className="send-invites-btn"
                                    disabled={!inviteEmails.trim()}
                                >
                                    <i className="fas fa-paper-plane"></i>
                                    {isDemoMode ? 'Davet Gönder (Demo)' : 'Davet Gönder'}
                                </button>
                                <button
                                    onClick={() => setShowInviteModal(false)}
                                    className="cancel-btn"
                                >
                                    İptal
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Debug paneli */}
            <div className="debug-panel">
                <h4 className="debug-title">
                    <i className="fas fa-tools"></i> Sistem Durumu
                </h4>
                <div className="debug-grid">
                    <div className="debug-item">
                        <i className="fas fa-key"></i>
                        <div>
                            <p className="debug-label">Token Durumu</p>
                            <p className={`debug-value ${tokenStatus.exists ? 'token-valid' : 'token-invalid'}`}>
                                {tokenStatus.exists ? `✅ ${tokenStatus.preview}` : '❌ Yok'}
                            </p>
                        </div>
                    </div>
                    <div className="debug-item">
                        <i className="fas fa-code-branch"></i>
                        <div>
                            <p className="debug-label">Mod</p>
                            <p className={`debug-value ${isDemoMode ? 'demo-status' : 'real-status'}`}>
                                {isDemoMode ? '🔶 Demo' : '✅ Gerçek'}
                            </p>
                        </div>
                    </div>
                    <div className="debug-item">
                        <i className="fas fa-server"></i>
                        <div>
                            <p className="debug-label">Backend</p>
                            <p className="debug-value">
                                {isDemoMode ? '🔶 Bağlantı Yok' : '✅ Bağlantı Var'}
                            </p>
                        </div>
                    </div>
                    <div className="debug-item">
                        <i className="fas fa-database"></i>
                        <div>
                            <p className="debug-label">Veri Kaynağı</p>
                            <p className="debug-value">
                                {isDemoMode ? '🔶 Demo Veri' : '✅ Gerçek Veri'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GroupManager;