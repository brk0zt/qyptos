import React from "react";
import { useAuth } from "../AuthContext"; // AuthContext'i import et

const ChunkDownloader = ({ apiBase, userEmail }) => {
    const { user } = useAuth(); // AuthContext'ten kullanıcı bilgilerini al

    return (
        <div className="p-6 bg-white rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-4">Chunk Downloader</h2>
            <p className="text-gray-600">Downloader bileşeni buraya gelecek.</p>
            <p className="mt-2 text-sm text-gray-500">API: {apiBase}</p>
            <p className="text-sm text-gray-500">Kullanıcı: {userEmail}</p>
            <p className="text-sm text-gray-500">Auth Kullanıcı: {user ? user.email : 'Kullanıcı yok'}</p>
        </div>
    );
};

export default ChunkDownloader;
