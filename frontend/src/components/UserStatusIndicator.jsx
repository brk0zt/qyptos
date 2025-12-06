import React, { useEffect, useState } from "react";
import { connectPresence, onPresenceUpdate } from "../utils/presenceSocket";

export default function UserStatusIndicator({ username }) {
    const [status, setStatus] = useState("offline");

    useEffect(() => {
        connectPresence((data) => {
            if (data.user === username) {
                setStatus(data.status);
            }
        });

        onPresenceUpdate((data) => {
            if (data.user === username) {
                setStatus(data.status);
            }
        });
    }, [username]);

    return (
        <div className="flex items-center gap-2">
            <div
                className={`w-3 h-3 rounded-full ${status === "online" ? "bg-green-500" : "bg-gray-400"
                    }`}
            ></div>
            <span className="text-sm text-gray-700">{username}</span>
        </div>
    );
}
