// ChatContainer.jsx - GÜNCELLENMİŞ
import React, { useState } from "react";
import UserList from "./UserList";
import ChatBox from "./ChatBox";
import "./ChatContainer.css";

export default function ChatContainer({ currentUser }) {
    const [selectedUser, setSelectedUser] = useState(null);
    const [users] = useState([
        { id: 1, username: "bıküzı", is_online: true, last_seen: null },
        { id: 2, username: "burak2", is_online: true, last_seen: null }
    ]);

    const [showSearch, setShowSearch] = useState(false);
    const [showInfo, setShowInfo] = useState(false);

    // currentUser'ın string olduğundan emin ol
    const currentUsername = typeof currentUser === 'string' ? currentUser : currentUser?.username || 'user';

    const handleSearch = () => {
        setShowSearch(true);
        console.log("Arama açıldı");
    };

    const handleInfo = () => {
        setShowInfo(true);
        console.log("Bilgi açıldı", selectedUser);
    };

    const handleSelectUser = (user) => {
        console.log("Seçilen kullanıcı:", user);
        setSelectedUser(user);
    };

    return (
        <div className="chat-container">
            {/* Sidebar - Kullanıcı Listesi */}
            <div className="chat-sidebar">
                <UserList
                    users={users}
                    currentUser={currentUsername}
                    onSelectUser={handleSelectUser}
                />
            </div>

            {/* Ana İçerik - Sohbet Kutusu */}
            <div className="chat-main">
                {selectedUser ? (
                    <div className="chat-session">
                        <div className="chat-header">
                            <div className="chat-user-info">
                                <div className="user-avatar-mini">
                                    {selectedUser.username?.charAt(0).toUpperCase()}
                                </div>
                                <div className="user-details">
                                    <h3>{selectedUser.username}</h3>
                                    <span className={`user-status ${selectedUser.is_online ? 'online' : 'offline'}`}>
                                        ● {selectedUser.is_online ? 'Çevrimiçi' : 'Çevrimdışı'}
                                    </span>
                                </div>
                            </div>
                            <div className="chat-actions">
                                <button
                                    className="icon-btn"
                                    title="Arama"
                                    onClick={handleSearch}
                                >
                                    <i className="fas fa-search"></i>
                                </button>
                                <button
                                    className="icon-btn"
                                    title="Bilgi"
                                    onClick={handleInfo}
                                >
                                    <i className="fas fa-info-circle"></i>
                                </button>
                                <button className="icon-btn" title="Daha fazla">
                                    <i className="fas fa-ellipsis-v"></i>
                                </button>
                            </div>
                        </div>
                        <ChatBox
                            threadId={selectedUser.id}
                            currentUser={currentUsername}
                            selectedUser={selectedUser}
                        />
                    </div>
                ) : (
                    <div className="welcome-screen">
                        <div className="welcome-content">
                            <div className="welcome-icon">
                                <i className="fas fa-comments"></i>
                            </div>
                            <h2>Sohbete Başlayın</h2>
                            <p>Soldaki listeden bir kullanıcı seçerek sohbet etmeye başlayın</p>
                            <div className="welcome-stats">
                                <div className="stat-item">
                                    <span className="stat-number">{users.length}</span>
                                    <span className="stat-label">Toplam Kullanıcı</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-number">
                                        {users.filter(u => u.is_online).length}
                                    </span>
                                    <span className="stat-label">Çevrimiçi</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Modal'lar aynı kalacak */}
            {showSearch && (
                <div className="modal-overlay" onClick={() => setShowSearch(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Mesajlarda Ara</h3>
                            <button className="close-btn" onClick={() => setShowSearch(false)}>
                                <i className="fas fa-times"></i>
                            </button>
                        </div>
                        <div className="search-input-container">
                            <input
                                type="text"
                                placeholder="Mesajlarda ara..."
                                className="search-input-modal"
                            />
                            <button className="search-btn">
                                <i className="fas fa-search"></i>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {showInfo && selectedUser && (
                <div className="modal-overlay" onClick={() => setShowInfo(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Kullanıcı Bilgisi</h3>
                            <button className="close-btn" onClick={() => setShowInfo(false)}>
                                <i className="fas fa-times"></i>
                            </button>
                        </div>
                        <div className="user-info-content">
                            <div className="user-avatar-large">
                                {selectedUser.username?.charAt(0).toUpperCase()}
                            </div>
                            <h4>{selectedUser.username}</h4>
                            <p className={`user-status-info ${selectedUser.is_online ? 'online' : 'offline'}`}>
                                {selectedUser.is_online ? 'Çevrimiçi' : 'Çevrimdışı'}
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}