let socket = null;
let listeners = [];

export function connectNotifications(userId, onMessage) {
    socket = new WebSocket(`ws://127.0.0.1:8001/ws/notifications/`);

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("Yeni bildirim:", data);
        if (onMessage) onMessage(data);
        listeners.forEach((cb) => cb(data));
    };

    socket.onopen = () => console.log("🔗 Bildirim soketi bağlı!");
    socket.onclose = () => console.log("❌ Bildirim soketi kapandı!");
}

export function onNotification(cb) {
    listeners.push(cb);
}
