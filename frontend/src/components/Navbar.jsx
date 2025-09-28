import { useNavigate } from "react-router-dom";
import React, { useState, useEffect } from "react";
import { useAuth } from "../AuthContext";
import { Button } from "./ui/Button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Avatar, AvatarFallback } from "./ui/Avatar";
import { Bell } from "lucide-react";
import { useApi } from "../utils/api";

export default function Navbar({ onProfileClick }) {
    const { user, logout } = useAuth();
    const { apiFetch } = useApi();
    const navigate = useNavigate();
    const [notifications, setNotifications] = useState([]);

    const handleClickNotification = async (id, targetUrl) => {
        await handleMarkAsRead(id);
        if (targetUrl) {
            navigate(targetUrl);
        }
    };


    useEffect(() => {
        const loadNotifications = async () => {
            try {
                const response = await fetch('http://localhost:8001/notifications/', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',  // Önemli: cookie'leri include et
                });

                if (response.ok) {
                    const data = await response.json();
                    setNotifications(data);
                } else {
                    console.error('Bildirimler yüklenemedi:', response.status);
                }
            } catch (error) {
                console.error('Bildirim yükleme hatası:', error);
                // Hata durumunda boş array set et
                setNotifications([]);
            }
        };

        if (user) {
            loadNotifications();
        }
    }, [user]);

    const handleMarkAllAsRead = async () => {
        try {
            const res = await apiFetch("/notifications/read-all/", {
                method: "PATCH",
            });
            if (res.ok) {
                setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
            }
        } catch (error) {
            console.error("Okundu işaretleme hatası:", error);
        }
    };

    const handleMarkAsRead = async (notificationId) => {
        try {
            const res = await apiFetch(`/notifications/${notificationId}/read/`, {
                method: "PATCH",
            });
            if (res.ok) {
                setNotifications((prev) =>
                    prev.map((n) =>
                        n.id === notificationId ? { ...n, is_read: true } : n
                    )
                );
            }
        } catch (error) {
            console.error("Bildirim okundu işaretleme hatası:", error);
        }
    };

    // WebSocket bağlantısını App.js'de yapıyoruz, burada gerek yok

    return (
        <div className="w-full h-14 bg-white shadow flex items-center justify-between px-6">
            <h1 className="text-xl font-bold">☁️ Cloud MVP</h1>

            <div className="flex items-center gap-6">
                {/* Bildirimler */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <div className="relative cursor-pointer">
                            <Bell className="h-6 w-6 text-gray-700" />
                            {notifications.filter(n => !n.is_read).length > 0 && (
                                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs px-1 rounded-full">
                                    {notifications.filter(n => !n.is_read).length}
                                </span>
                            )}
                        </div>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-64">
                        <DropdownMenuLabel>Bildirimler</DropdownMenuLabel>
                        <DropdownMenuSeparator />

                        {notifications.filter(n => !n.is_read).length > 0 && (
                            <>
                                <DropdownMenuItem
                                    className="text-blue-600 cursor-pointer"
                                    onClick={handleMarkAllAsRead}
                                >
                                    ✅ Tümünü okundu yap
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                            </>
                        )}

                        {notifications.length === 0 ? (
                            <DropdownMenuItem className="text-gray-500">
                                Henüz bildiriminiz yok
                            </DropdownMenuItem>
                        ) : (
                            notifications.slice(0, 5).map((n) => (
                                <DropdownMenuItem
                                    key={n.id}
                                    className={n.is_read ? "text-gray-400" : "font-medium"}
                                    onClick={() => handleMarkAsRead(n.id)}
                                >
                                    {n.text || n.message}
                                </DropdownMenuItem>
                            ))
                        )}
                    </DropdownMenuContent>
                </DropdownMenu>

                {/* Kullanıcı Menüsü */}
                {user && (
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <div className="flex items-center gap-2 cursor-pointer">
                                <Avatar className="h-8 w-8">
                                    <AvatarFallback>
                                        {user.username ? user.username[0].toUpperCase() : "U"}
                                    </AvatarFallback>
                                </Avatar>
                                <span className="font-medium">{user.username}</span>
                            </div>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-40">
                            <DropdownMenuLabel>Hesap</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={onProfileClick}>👤 Profil</DropdownMenuItem>
                            <DropdownMenuItem onClick={logout} className="text-red-600">
                                🚪 Çıkış
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                )}
            </div>
        </div>
    );
}



