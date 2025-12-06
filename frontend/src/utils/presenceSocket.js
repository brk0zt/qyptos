let presenceSocket = null;
let listeners = [];

export function connectPresence(onUpdate) {
    presenceSocket = new WebSocket(`ws://127.0.0.1:8001/ws/presence/`);

    presenceSocket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (onUpdate) onUpdate(data);
        listeners.forEach((cb) => cb(data));
    };

    presenceSocket.onopen = () => console.log("🟢 Presence soketi bagli");
    presenceSocket.onclose = () => console.log("⚫ Presence soketi kapandi");
}

export function onPresenceUpdate(cb) {
    listeners.push(cb);
}

