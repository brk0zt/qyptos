// Dashboard.jsx
import React, { useState } from "react";
import { useAuth } from "../AuthContext";
import ChunkDownloader from "./ChunkDownloader";
import GroupContent from "./GroupContent";
import AdPlayer from "./AdPlayer";
import SingleViewMedia from "./SingleViewMedia";
import Profile from "./Profile";
import "./styles/Dashboard.css";
import QyptosLogo from "./banner_logo.png";

export default function Dashboard() {
    const auth = useAuth();
    const [active, setActive] = useState("downloader");
    const [notificationCount, setNotificationCount] = useState(3);

    const handleLogout = () => {
        auth.logout();
    };

    const renderContent = () => {
        switch (active) {
            case "downloader":
                return <ChunkDownloader />;
            case "groups":
                return <GroupContent />;
            case "search_engine":
                return <SearchEngine />;
            case "media":
                return <SingleViewMedia />;
            case "profile":
                return <Profile />;
            default:
                return <div className="content-placeholder">Bir içerik seçin</div>;
        }
    };

    return (
        <div className="dashboard-horizontal">
            {/* Üst Navigasyon Bar */}
            <nav className="top-nav">
                <div className="nav-left">
                    <div className="logo">
                        <img src={QyptosLogo} alt="QYPTOS Logo" className="qyptos-logo-img" />
                    </div>

                    <div className="nav-menu">
                        <div
                            className={`nav-item ${active === "downloader" ? "active" : ""}`}
                            onClick={() => setActive("downloader")}
                        >
                            <i className="fas fa-download"></i>
                            <span>Downloader</span>
                        </div>
                        <div
                            className={`nav-item ${active === "groups" ? "active" : ""}`}
                            onClick={() => setActive("groups")}
                        >
                            <i className="fas fa-users"></i>
                            <span>Gruplar</span>
                        </div>
                        <div
                            className={`nav-item ${active === "search_engine" ? "active" : ""}`}
                            onClick={() => setActive("search_engine")}
                        >
                            <i className="fas fa-search"></i>
                            <span>Ara</span>
                        </div>
                        <div
                            className={`nav-item ${active === "trends" ? "active" : ""}`}
                            onClick={() => setActive("trends")}
                        >
                            <i className="fas fa-fire"></i>
                            <span>Trendler</span>
                        </div>
                        <div
                            className={`nav-item ${active === "media" ? "active" : ""}`}
                            onClick={() => setActive("media")}
                        >
                            <i className="fas fa-photo-video"></i>
                            <span>Medya</span>
                        </div>
                    </div>
                </div>

                <div className="nav-right">
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
                        <span className="user-name">Burak</span>
                        <i className="fas fa-chevron-down"></i>

                        <div className="dropdown-menu">
                            <div className="dropdown-item">
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

