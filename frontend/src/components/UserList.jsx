// UserList.jsx - GÜNCELLENMİŞ
import React, { useState, useMemo } from "react";
import "./UserList.css";

export default function UserList({ users, currentUser, onSelectUser }) {
    const [searchTerm, setSearchTerm] = useState("");

    // currentUser'ın string olduğundan emin ol
    const currentUsername = typeof currentUser === 'string' ? currentUser : currentUser?.username || 'user';

    const sortedAndFilteredUsers = useMemo(() => {
        let filtered = users;

        if (searchTerm) {
            filtered = users.filter(user =>
                user.username.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        return filtered.sort((a, b) => {
            if (a.is_online && !b.is_online) return -1;
            if (!a.is_online && b.is_online) return 1;
            return a.username.localeCompare(b.username);
        });
    }, [users, searchTerm]);

    const onlineCount = users.filter(user => user.is_online).length;
    const totalCount = users.length;

    return (
        <div className="user-list-container">
            <div className="user-list-header">
                <div>
                    <h3>Kullanıcılar</h3>
                    <div className="user-stats">
                        <span className="online-count">{onlineCount} çevrimiçi</span>
                        <span className="total-count">{totalCount} toplam</span>
                    </div>
                </div>
            </div>

            <div className="user-search">
                <input
                    type="text"
                    placeholder="Kullanıcı ara..."
                    className="search-input"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
                {searchTerm && (
                    <button
                        className="clear-search"
                        onClick={() => setSearchTerm("")}
                    >
                        ✕
                    </button>
                )}
            </div>

            <div className="user-list">
                {sortedAndFilteredUsers.length > 0 ? (
                    sortedAndFilteredUsers.map((user) => (
                        <div
                            key={user.id}
                            className={`user-item ${user.is_online ? 'online' : 'offline'}`}
                            onClick={() => onSelectUser(user.username)}
                        >
                            <div className="user-avatar">
                                <div className="avatar-circle">
                                    {user.username.charAt(0).toUpperCase()}
                                </div>
                                <div className={`status-indicator ${user.is_online ? 'online' : 'offline'}`}></div>
                            </div>

                            <div className="user-info">
                                <span className="username">{user.username}</span>
                                <span className="user-status-text">
                                    {user.is_online ? 'Çevrimiçi' : 'Çevrimdışı'}
                                </span>
                            </div>

                            <div className="user-actions">
                                <button
                                    className="message-btn"
                                    title="Mesaj gönder"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onSelectUser(user);
                                    }}
                                >
                                    <i className="fas fa-comment"></i>
                                </button>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="no-users">
                        <div className="no-users-icon">👥</div>
                        <p>{searchTerm ? 'Aranan kullanıcı bulunamadı' : 'Henüz kullanıcı yok'}</p>
                        {!searchTerm && (
                            <button
                                className="refresh-btn"
                                onClick={() => window.location.reload()}
                            >
                                Sayfayı Yenile
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}