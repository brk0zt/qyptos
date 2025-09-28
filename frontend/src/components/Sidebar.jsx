// Sidebar.jsx
import React from "react";

export default function Sidebar({ active, setActive, onLogout }) {
    const menuItems = [
        { key: "downloader", icon: "fas fa-download", label: "Downloader" },
        { key: "groups", icon: "fas fa-users", label: "Gruplar" },
        { key: "ads", icon: "fas fa-ad", label: "Reklamlar" },
        { key: "media", icon: "fas fa-photo-video", label: "Medya" },
        { key: "profile", icon: "fas fa-user-circle", label: "Profil" },
    ];

    return (
        <div className="sidebar">
            <div className="logo">
                <i className="fas fa-cloud"></i>
                <h1>Cloud MVP</h1>
            </div>

            <div className="menu">
                {menuItems.map(item => (
                    <div
                        key={item.key}
                        className={`menu-item ${active === item.key ? 'active' : ''}`}
                        onClick={() => setActive(item.key)}
                    >
                        <i className={item.icon}></i>
                        <span>{item.label}</span>
                    </div>
                ))}

                <div className="divider"></div>

                <div className="menu-item" onClick={onLogout}>
                    <i className="fas fa-sign-out-alt"></i>
                    <span>Çıkış Yap</span>
                </div>
            </div>
        </div>
    );
}
