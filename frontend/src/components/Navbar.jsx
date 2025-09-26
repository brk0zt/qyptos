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
    const [notifications, setNotifications] = useState([]);

    useEffect(() => {
        const loadNotifications = async () => {
            const res = await apiFetch("http://127.0.0.1:8000/notifications/");
            if (res.ok) {
                const data = await res.json();
                setNotifications(data);
            }
        };
        if (user) loadNotifications();
    }, [user, apiFetch]);

    const handleMarkAllAsRead = async () => {
        const res = await apiFetch("http://127.0.0.1:8000/notifications/read-all/", {
            method: "PATCH",
        });
        if (res.ok) {
            setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
        }
    };

    useEffect(() => {
        if (!user) return;

        // WebSocket bağlan
        const ws = new WebSocket("ws://127.0.0.1:8000/ws/notifications/");

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setNotifications((prev) => [data, ...prev]);
        };

        ws.onclose = () => {
            console.log("🔌 WebSocket bağlantısı kapandı");
        };

        return () => ws.close();
    }, [user]);


    return (
        <div className="w-full h-14 bg-white shadow flex items-center justify-between px-6">
            <h1 className="text-xl font-bold">☁️ Cloud MVP</h1>

            <div className="flex items-center gap-6">
                {/* Bildirimler */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <div className="relative cursor-pointer">
                            <Bell className="h-6 w-6 text-gray-700" />
                            {notifications.length > 0 && (
                                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs px-1 rounded-full">
                                    {notifications.length}
                                </span>
                            )}
                        </div>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-64">
                        <DropdownMenuLabel>Bildirimler</DropdownMenuLabel>
                        <DropdownMenuSeparator />

                        {notifications.length > 0 && (
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
                            notifications.map((n) => (
                                <DropdownMenuItem
                                    key={n.id}
                                    className={n.is_read ? "text-gray-400" : "font-medium"}
                                    onClick={() => handleMarkAsRead(n.id)}
                                >
                                    {n.text}
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




