import React, { useState } from "react";
import { useAuth } from "../AuthContext";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import ChunkDownloader from "./ChunkDownloader";
import GroupContent from "./GroupContent";
import AdPlayer from "./AdPlayer";
import SingleViewMedia from "./SingleViewMedia";
import Profile from "./Profile";


export default function Dashboard() {
    const auth = useAuth();
    const [active, setActive] = useState("downloader");
    const apiBase = "http://localhost:8001/api";

    const handleLogout = () => {
        auth.logout(); // Bu, login sayfasına yönlendirmeyi tetikleyecek
    };

    const renderContent = () => {
        switch (active) {
            case "downloader":
                return <ChunkDownloader />;
            case "groups":
                return <GroupContent />;
            case "ads":
                return <AdPlayer />;
            case "media":
                return <SingleViewMedia />;
            case "profile":
                return <Profile />;
            default:
                return <div className="p-4">Bir içerik seçin</div>;
        }
        
    };

    return (
        <div className="flex h-screen bg-gray-100 font-sans">
            {/* Soldaki Sidebar */}
            <Sidebar active={active} setActive={setActive} onLogout={handleLogout} />

            {/* Sağdaki Ana İçerik Alanı */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Üstteki Navbar */}
                <Navbar />

                {/* Dinamik İçerik Alanı */}
                <div className="flex-1 overflow-y-auto p-4 bg-white">
                    {renderContent()}
                </div>
            </div>
        </div>
    );
}

