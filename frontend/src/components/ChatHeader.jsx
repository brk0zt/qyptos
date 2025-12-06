import React from "react";
import UserStatusIndicator from "./UserStatusIndicator";

export default function ChatHeader({ username, isOnline }) {
    return (
        <div className="chat-header">
            <div className="chat-user-info">
                <UserStatusIndicator username={username} isOnline={isOnline} />
                <div className="chat-status">
                    <span className={`status-text ${isOnline ? 'online' : 'offline'}`}>
                        {isOnline ? 'Çevrimiçi' : 'Çevrimdışı'}
                    </span>
                </div>
            </div>
            <div className="chat-actions">
                <button className="header-btn" title="Arama">
                    <i className="fas fa-search"></i>
                </button>
                <button className="header-btn" title="Bilgi">
                    <i className="fas fa-info-circle"></i>
                </button>
            </div>
        </div>
    );
}
