import React, { useEffect, useState } from "react";
import { useApi } from "../utils/api";
import CommentCard from "./CommentCard";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";

export default function CommentSection({ fileId }) {
    const { apiFetch } = useApi();
    const [comments, setComments] = useState([]);
    const [sort, setSort] = useState("new");

    const loadComments = async () => {
        const res = await apiFetch(`http://127.0.0.1:8001/groups/files/${fileId}/comments/?sort=${sort}`);
        if (res.ok) {
            const data = await res.json();
            setComments(data);
        }
    };

    useEffect(() => {
        loadComments();
    }, [sort]);

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h3 className="font-semibold text-lg">💬 Yorumlar</h3>
                <div className="w-40">
                    <Select value={sort} onValueChange={setSort}>
                        <SelectTrigger>
                            <SelectValue placeholder="Sırala" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="new">🕓 Yeni</SelectItem>
                            <SelectItem value="top">🔥 Popüler</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {comments.length === 0 ? (
                <p className="text-gray-500">Henüz yorum yok.</p>
            ) : (
                comments.map((c) => <CommentCard key={c.id} comment={c} />)
            )}
        </div>
    );
}
