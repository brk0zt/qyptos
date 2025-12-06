import React, { useState, useEffect } from "react";
import { Input } from "./ui/Input";
import { Card } from "./ui/Card";
import { useApi } from "../utils/api";

export default function CommentInput({ onSubmit }) {
    const { apiFetch } = useApi();
    const [text, setText] = useState("");
    const [users, setUsers] = useState([]);
    const [mentionSuggestions, setMentionSuggestions] = useState([]);

    // tüm kullanıcıları al (mock olarak ya da backend’den)
    useEffect(() => {
        const loadUsers = async () => {
            const res = await apiFetch("http://127.0.0.1:8001/users/");
            if (res.ok) {
                const data = await res.json();
                setUsers(data);
            }
        };
        loadUsers();
    }, []);

    // mention önerisi
    useEffect(() => {
        const lastWord = text.split(" ").pop();
        if (lastWord.startsWith("@")) {
            const query = lastWord.substring(1).toLowerCase();
            const matches = users.filter((u) =>
                u.username.toLowerCase().startsWith(query)
            );
            setMentionSuggestions(matches.slice(0, 5));
        } else {
            setMentionSuggestions([]);
        }
    }, [text]);

    return (
        <div className="relative">
            <Input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Yorum yaz (örnek: @burak...)"
                className="pr-2"
            />
            {mentionSuggestions.length > 0 && (
                <Card className="absolute top-full left-0 w-full z-10 shadow-md bg-white">
                    {mentionSuggestions.map((u) => (
                        <div
                            key={u.id}
                            className="p-2 hover:bg-gray-100 cursor-pointer"
                            onClick={() => {
                                const words = text.split(" ");
                                words[words.length - 1] = `@${u.username}`;
                                setText(words.join(" ") + " ");
                                setMentionSuggestions([]);
                            }}
                        >
                            @{u.username}
                        </div>
                    ))}
                </Card>
            )}
            <button
                className="mt-2 bg-blue-500 text-white px-4 py-1 rounded"
                onClick={() => {
                    onSubmit(text);
                    setText("");
                }}
            >
                Gönder
            </button>
        </div>
    );
}
