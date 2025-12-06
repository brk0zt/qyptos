// ChatBox.jsx - FIXED
import React, { useState, useEffect, useRef } from "react";
import "./ChatBox.css";

export default function ChatBox({ threadId, currentUser, selectedUser }) {
    const [messages, setMessages] = useState([]);
    const [text, setText] = useState("");
    const [file, setFile] = useState(null);
    const [socket, setSocket] = useState(null);
    const endRef = useRef(null);

    // currentUser'ın string olduğundan emin ol
    const currentUsername = typeof currentUser === 'string' ? currentUser : currentUser?.username || 'user';

    // WebSocket connection
    useEffect(() => {
        if (!threadId) return;

        const ws = new WebSocket(`ws://127.0.0.1:8000/ws/chat/${threadId}/`);

        ws.onopen = () => {
            console.log('WebSocket connected');
        };

        ws.onmessage = (e) => {
            const data = JSON.parse(e.data);

            if (data.type === "reaction") {
                setMessages((prev) =>
                    prev.map((m) => {
                        if (m.id === data.id) {
                            let reactions = m.reactions ? [...m.reactions] : [];
                            const existingIndex = reactions.findIndex(
                                (r) => r.user === data.user && r.emoji === data.emoji
                            );
                            if (data.action === "added" && existingIndex === -1) {
                                reactions.push({ user: data.user, emoji: data.emoji });
                            } else if (data.action === "removed" && existingIndex !== -1) {
                                reactions.splice(existingIndex, 1);
                            }
                            return { ...m, reactions };
                        }
                        return m;
                    })
                );
            } else if (data.type === "delete") {
                setMessages((prev) => prev.filter((m) => m.id !== data.id));
            } else if (data.type === "edit") {
                setMessages((prev) =>
                    prev.map((m) =>
                        m.id === data.id ? { ...m, message: data.text, edited: true } : m
                    )
                );
            } else if (data.type === "read") {
                setMessages((prev) =>
                    prev.map((m) =>
                        m.id === data.id ? { ...m, read: true } : m
                    )
                );
            } else {
                setMessages((prev) => [...prev, data]);
            }
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
        };

        setSocket(ws);

        return () => {
            ws.close();
        };
    }, [threadId]);

    // Demo mesajları
    useEffect(() => {
        if (selectedUser) {
            const demoMessages = [
                {
                    id: 1,
                    sender: selectedUser.username,
                    message: "Selam! Nasılsın?",
                    timestamp: new Date(Date.now() - 300000).toISOString(),
                    status: 'seen'
                },
                {
                    id: 2,
                    sender: currentUsername,
                    message: "İyiyim, teşekkürler! Sen nasılsın?",
                    timestamp: new Date(Date.now() - 180000).toISOString(),
                    status: 'seen'
                },
                {
                    id: 3,
                    sender: selectedUser.username,
                    message: "Ben de iyiyim, sağ ol!",
                    timestamp: new Date(Date.now() - 60000).toISOString(),
                    status: 'delivered'
                }
            ];
            setMessages(demoMessages);
        } else {
            setMessages([]);
        }
    }, [selectedUser, currentUsername]);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Mark messages as read
    useEffect(() => {
        messages.forEach((msg) => {
            if (!msg.read && msg.sender !== currentUsername) {
                // Hem WebSocket hem API üzerinden gönderiyoruz
                socket?.send(JSON.stringify({ type: "read", id: msg.id }));
                fetch(`http://127.0.0.1:8000/chat/read/${msg.id}/`, {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("token")}`,
                    },
                });
            }
        });
    }, [messages, currentUsername, socket]);

    const sendFile = async () => {
        if (!file) return;

        try {
            const newMessage = {
                id: Date.now(),
                sender: currentUsername,
                message: "",
                file_url: URL.createObjectURL(file),
                timestamp: new Date().toISOString(),
                status: 'sent'
            };

            setMessages(prev => [...prev, newMessage]);
            setFile(null);

            setTimeout(() => {
                setMessages(prev =>
                    prev.map(m =>
                        m.id === newMessage.id ? { ...m, status: 'delivered' } : m
                    )
                );
            }, 500);
        } catch (error) {
            console.error("Dosya gönderilemedi:", error);
        }
    };

    const sendMessage = () => {
        if (text.trim() && socket) {
            // WebSocket üzerinden mesaj gönder
            socket.send(JSON.stringify({
                type: "message",
                message: text
            }));

            const newMessage = {
                id: Date.now(),
                sender: currentUsername,
                message: text,
                timestamp: new Date().toISOString(),
                status: 'sent'
            };

            setMessages(prev => [...prev, newMessage]);
            setText("");

            setTimeout(() => {
                setMessages(prev =>
                    prev.map(m =>
                        m.id === newMessage.id ? { ...m, status: 'delivered' } : m
                    )
                );

                setTimeout(() => {
                    setMessages(prev =>
                        prev.map(m =>
                            m.id === newMessage.id ? { ...m, status: 'seen' } : m
                        )
                    );
                }, 1000);
            }, 500);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'sent':
                return '✓';
            case 'delivered':
                return '✓✓';
            case 'seen':
                return '✓✓ ●';
            default:
                return '';
        }
    };

    const handleReaction = async (msg, emoji) => {
        if (!socket) return;

        const res = await fetch(`http://127.0.0.1:8000/chat/reaction/${msg.id}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
            body: JSON.stringify({ emoji }),
        });

        if (res.ok) {
            const data = await res.json();
            socket.send(
                JSON.stringify({
                    type: "reaction",
                    id: msg.id,
                    emoji: emoji,
                    action: data.action || "added",
                })
            );
        }
    };

    const renderMessage = (msg, index) => {
        const isMine = msg.sender === currentUsername;
        const emojis = ["❤️", "😂", "👍", "🔥", "😮", "😢"];

        return (
            <div
                key={msg.id || index}
                className={`message-bubble ${isMine ? 'own' : 'other'}`}
            >
                {!isMine && (
                    <div className="message-sender">{msg.sender}</div>
                )}

                {msg.message && (
                    <div className="message-text">
                        {msg.message}
                    </div>
                )}
                {msg.file_url && (
                    <div className="message-file">
                        {/\.(jpg|jpeg|png|gif|webp)$/i.test(msg.file_url) ? (
                            <img
                                src={msg.file_url}
                                alt="Dosya"
                                className="message-image"
                                onError={(e) => {
                                    e.target.style.display = 'none';
                                }}
                            />
                        ) : (
                            <a
                                href={msg.file_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="file-download-link"
                            >
                                <i className="fas fa-paperclip"></i>
                                Dosyayı indir
                            </a>
                        )}
                    </div>
                )}

                {/* Reactionlar */}
                {msg.reactions && msg.reactions.length > 0 && (
                    <div className="reactions-container">
                        {msg.reactions.map((r, idx) => (
                            <span
                                key={idx}
                                className="reaction-bubble"
                            >
                                {r.emoji}
                            </span>
                        ))}
                    </div>
                )}

                {/* Emoji butonları - sadece kendi mesajlarımız için */}
                {isMine && (
                    <div className="emoji-buttons">
                        {emojis.map((emoji) => (
                            <button
                                key={emoji}
                                onClick={() => handleReaction(msg, emoji)}
                                className="emoji-button"
                            >
                                {emoji}
                            </button>
                        ))}
                    </div>
                )}

                <div className="message-time">
                    {new Date(msg.timestamp).toLocaleTimeString('tr-TR', {
                        hour: '2-digit',
                        minute: '2-digit'
                    })}
                    {isMine && msg.status && (
                        <span className={`message-status ${msg.status}`}>
                            {getStatusIcon(msg.status)}
                        </span>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="modern-chat-container">
            <div className="messages-container">
                {messages.length > 0 ? (
                    messages.map(renderMessage)
                ) : (
                    <div className="empty-chat-state">
                        <div className="empty-chat-icon">
                            <i className="fas fa-comment-dots"></i>
                        </div>
                        <h3>Sohbete Başlayın</h3>
                        <p>{selectedUser?.username} ile mesajlaşmaya başlayın</p>
                    </div>
                )}
                <div ref={endRef} />
            </div>

            <div className="file-upload-section">
                <div className="file-input-wrapper">
                    <label className="file-input-label">
                        <i className="fas fa-paperclip"></i>
                        <span>{file ? file.name : 'Dosya seç...'}</span>
                        <input
                            type="file"
                            onChange={(e) => setFile(e.target.files[0])}
                            className="file-input-hidden"
                        />
                    </label>
                    {file && (
                        <button
                            onClick={sendFile}
                            className="send-file-btn"
                        >
                            <i className="fas fa-upload"></i>
                            Gönder
                        </button>
                    )}
                </div>
            </div>

            <div className="message-input-section">
                <div className="message-input-wrapper">
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Mesaj yazın..."
                        className="message-input"
                        rows="1"
                    />
                    <button
                        onClick={sendMessage}
                        disabled={!text.trim() || !socket}
                        className="send-message-btn"
                    >
                        <i className="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        </div>
    );
}