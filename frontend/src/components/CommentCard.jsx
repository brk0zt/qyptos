import React, { useState } from "react";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";
import { ThumbsUp, ThumbsDown, Reply } from "lucide-react";
import { useApi } from "../utils/api";

export default function CommentCard({ comment, depth = 0 }) {
    const { apiFetch } = useApi();
    const [likes, setLikes] = useState(comment.likes);
    const [dislikes, setDislikes] = useState(comment.dislikes);
    const [showReplyBox, setShowReplyBox] = useState(false);
    const [replyText, setReplyText] = useState("");
    const [replies, setReplies] = useState(comment.replies || []);

    const react = async (type) => {
        await apiFetch(`http://127.0.0.1:8001/groups/comments/${comment.id}/react/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ reaction: type }),
        });
        if (type === "like") setLikes(likes + 1);
        if (type === "dislike") setDislikes(dislikes + 1);
    };

    const submitReply = async () => {
        const res = await apiFetch(`http://127.0.0.1:8001/groups/comments/${comment.id}/reply/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: replyText }),
        });
        if (res.ok) {
            const data = await res.json();
            setReplies([...replies, data]);
            setReplyText("");
            setShowReplyBox(false);
        }
    };

    function highlightMentions(text) {
        const parts = text.split(/(@\w+)/g);
        return parts.map((part, i) =>
            part.startsWith("@") ? (
                <span key={i} className="text-blue-600 font-medium">
                    {part}
                </span>
            ) : (
                part
            )
        );
    }

    return (
        <div className="border rounded p-3 my-2 ml-[${depth * 20}px]">
            <p className="font-semibold">{comment.user}</p>
            <p>{comment.text}</p>
            <div className="flex gap-2 mt-2">
                <Button variant="ghost" size="sm" onClick={() => react("like")}>
                    <ThumbsUp className="w-4 h-4 mr-1" /> {likes}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => react("dislike")}>
                    <ThumbsDown className="w-4 h-4 mr-1" /> {dislikes}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setShowReplyBox(!showReplyBox)}>
                    <Reply className="w-4 h-4 mr-1" /> Yanıtla
                </Button>
            </div>

            {showReplyBox && (
                <div className="mt-2 flex gap-2">
                    <Input
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                        placeholder="Yanıt yaz..."
                    />
                    <Button size="sm" onClick={submitReply}>Gönder</Button>
                </div>
            )}

            {/* Alt yorumlar (recursive) */}
            {replies.length > 0 && (
                <div className="ml-4 mt-2">
                    {replies.map((r) => (
                        <CommentCard key={r.id} comment={r} depth={depth + 1} />
                    ))}
                </div>
            )}
        </div>
    );
}
