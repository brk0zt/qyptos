import React, { useState } from "react";
import { Button } from './ui/Button';
import { Download, Users, Monitor, PanelLeftClose, PanelLeftOpen, UserRound } from "lucide-react";

export default function Sidebar({ active, setActive }) {
    const [collapsed, setCollapsed] = useState(false);

    const menuItems = [
        { key: "downloader", label: "Downloader", icon: <Download className="h-4 w-4" /> },
        { key: "groups", label: "Groups", icon: <Users className="h-4 w-4" /> },
        { key: "ads", label: "Ads", icon: <Monitor className="h-4 w-4" /> },
        // Yeni menü öğesi eklendi
        { key: "profile", label: "Profile", icon: <UserRound className="h-4 w-4" /> },
    ];

    return (
        <div
            className={`${collapsed ? "w-16" : "w-52"
                } bg-white shadow h-full flex flex-col transition-all duration-300`}
        >
            <div className="flex items-center justify-between p-3 border-b">
                {!collapsed && <h2 className="text-lg font-bold">Menü</h2>}
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCollapsed(!collapsed)}
                    className="ml-auto"
                >
                    {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
                </Button>
            </div>

            <div className="flex-1 p-2 space-y-2">
                {menuItems.map((item) => (
                    <Button
                        key={item.key}
                        variant={active === item.key ? "default" : "ghost"}
                        className={`w-full justify-start ${collapsed ? "justify-center px-2" : ""}`}
                        onClick={() => setActive(item.key)}
                    >
                        {item.icon}
                        {!collapsed && <span className="ml-2">{item.label}</span>}
                    </Button>
                ))}
            </div>
        </div>
    );
}
