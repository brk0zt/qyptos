import React, { useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { connectNotifications, onNotification } from "../utils/notificationSocket";
import { Card } from "./ui/Card";
import { Button } from "./ui/Button";
import { useApi } from "../utils/api";

export default function NotificationBell({ userId }) {
    const { apiFetch } = useApi();
    const [notifs, setNotifs] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);

    // WebSocket bağlantısı
    useEffect(() => {
        connectNotifications(userId, (msg) => {
            setNotifs((prev) => [{ ...msg, read: false }, ...prev]);
        });
        onNotification((msg) => setNotifs((prev) => [{ ...msg, read: false }, ...prev]));
    }, []);

    // Backend'den mevcut bildirimleri al
    useEffect(() => {
        const loadNotifs = async () => {
            const res = await apiFetch("http://127.0.0.1:8001/notifications/");
            if (res.ok) {
                const data = await res.json();
                setNotifs(data);
            }
        };
        loadNotifs();
    }, []);

    const markAllRead = async () => {
        const res = await apiFetch("http://127.0.0.1:8001/notifications/mark-read/", { method: "POST" });
        if (res.ok) {
            setNotifs((prev) => prev.map((n) => ({ ...n, read: true })));
        }
    };

    const unreadCount = notifs.filter((n) => !n.read).length;

    return (
        <div className="relative">
            <div className="cursor-pointer" onClick={() => setShowDropdown(!showDropdown)}>
                <Bell className="w-6 h-6 text-gray-700" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs px-1 rounded-full">
                        {unreadCount}
                    </span>
                )}
            </div>

            {showDropdown && (
                <Card className="absolute right-0 mt-2 w-72 bg-white shadow-lg p-3 z-20 space-y-2">
                    <div className="flex justify-between items-center mb-1">
                        <h3 className="font-semibold">🔔 Bildirimler</h3>
                        {unreadCount > 0 && (
                            <Button variant="ghost" size="sm" onClick={markAllRead}>
                                Tümünü oku
                            </Button>
                        )}
                    </div>

                    {notifs.length === 0 ? (
                        <p className="text-gray-500 text-sm">Henüz bildirim yok.</p>
                    ) : (
                        <div className="max-h-64 overflow-y-auto">
                            {notifs.map((n, i) => (
                                <div
                                    key={i}
                                    className={`text-sm border-b pb-1 mb-1 ${n.read ? "text-gray-500" : "text-black font-medium"
                                        }`}
                                >
                                    {n.message}
                                    <div className="text-xs text-gray-400">
                                        {new Date(n.created_at).toLocaleString()}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </Card>
            )}
        </div>
    );
}
