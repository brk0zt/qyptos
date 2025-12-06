import React, { useEffect, useState } from "react";
import { useAuth } from "../AuthContext";

export default function Profile() {
    const { token, user } = useAuth();
    const [profile, setProfile] = useState(null);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const res = await fetch("http://127.0.0.1:8001/auth/profile/", {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (res.ok) {
                    const data = await res.json();
                    setProfile(data);
                } else {
                    setError("Yetkisiz erişim veya token hatası.");
                }
            } catch (err) {
                setError("Sunucuya bağlanırken hata oluştu.");
            }
        };

        if (token) fetchProfile();
    }, [token]);

    if (error) return <div className="chunk-downloader"><p className="text-red-500">{error}</p></div>;
    if (!profile) return <div className="chunk-downloader"><p>Yükleniyor...</p></div>;

    return (
        <div className="chunk-downloader">
            <h2><i className="fas fa-user"></i> Profil Bilgileri</h2>
            <div className="user-section">
                <h4>Kullanıcı Bilgileri:</h4>
                <p><strong>ID:</strong> {profile.id}</p>
                <p><strong>Kullanıcı Adı:</strong> {profile.username}</p>
                <p><strong>E-posta:</strong> {profile.email}</p>
            </div>
        </div>
    );
}
