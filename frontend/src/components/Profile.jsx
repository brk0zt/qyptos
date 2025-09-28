import React, { useEffect, useState } from "react";
import { useAuth } from "../AuthContext";
import { useApi } from "../utils/api";

export default function Profile() {
    const { token } = useAuth();
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

    useEffect(() => {
        const loadProfile = async () => {
            const res = await apiFetch("http://127.0.0.1:8001/auth/profile/");
            if (res.ok) {
                const data = await res.json();
                setProfile(data);
            }
        };
        loadProfile();
    }, [apiFetch]);

    if (!profile) return <p>Yükleniyor...</p>;

    return (
        <div className="p-4 bg-white rounded shadow">
            <h2 className="text-lg font-bold mb-2">👤 Profil Bilgileri</h2>
            <p><b>ID:</b> {profile.id}</p>
            <p><b>Kullanıcı Adı:</b> {profile.username}</p>
            <p><b>E-posta:</b> {profile.email}</p>
        </div>
    );

    if (error) return <p className="text-red-500">{error}</p>;
    if (!profile) return <p>Yükleniyor...</p>;

    return (
        <div className="p-4 bg-white rounded shadow">
            <h2 className="text-lg font-bold mb-2">👤 Profil Bilgileri</h2>
            <p><b>ID:</b> {profile.id}</p>
            <p><b>Kullanıcı Adı:</b> {profile.username}</p>
            <p><b>E-posta:</b> {profile.email}</p>
        </div>
    );
}
