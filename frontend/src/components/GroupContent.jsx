import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardContent } from './ui/Card';
;
import { Input } from "./Input";
import { Button } from './ui/Button';
import { Textarea } from "./Textarea";
import SingleViewMedia from "./SingleViewMedia"; 

const GroupContent = ({ groupId, apiBase, userEmail }) => {
    const [authorized, setAuthorized] = useState(false);
    const [files, setFiles] = useState([]);
    const [comments, setComments] = useState({});
    const [newComment, setNewComment] = useState("");
    const [selectedFileId, setSelectedFileId] = useState(null);

    useEffect(() => {
        const checkAuthAndFetchFiles = async () => {
            try {
                const res = await fetch(`${apiBase}/groups/${groupId}/check-auth/?user=${userEmail}`);
                const data = await res.json();
                if (data.authorized) {
                    setAuthorized(true);
                    // Yetki başarılıysa dosyaları getir
                    const filesRes = await fetch(`${apiBase}/groups/${groupId}/files/`);
                    const filesData = await filesRes.json();
                    setFiles(filesData);
                } else {
                    setAuthorized(false);
                }
            } catch (error) {
                console.error(error);
                setAuthorized(false);
            }
        };

        checkAuthAndFetchFiles();
    }, [apiBase, groupId, userEmail]);

    const handleUpload = async (e) => {
        if (!authorized) return;
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("uploader", userEmail);

        try {
            await fetch(`${apiBase}/groups/${groupId}/files/`, {
                method: "POST",
                body: formData,
            });

            // Dosya listesini güncelle
            const updated = await fetch(`${apiBase}/groups/${groupId}/files/`).then((r) =>
                r.json()
            );
            setFiles(updated);
        } catch (error) {
            console.error("Dosya yükleme hatası:", error);
        }
    };

    const fetchComments = async (fileId) => {
        setSelectedFileId(fileId);
        try {
            const res = await fetch(`${apiBase}/groups/files/${fileId}/comments/`);
            const data = await res.json();
            setComments((prev) => ({ ...prev, [fileId]: data }));
        } catch (error) {
            console.error("Yorumlar yüklenirken hata:", error);
        }
    };

    const postComment = async () => {
        if (!authorized || !selectedFileId || !newComment.trim()) return;
        try {
            await fetch(`${apiBase}/groups/files/${selectedFileId}/comments/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: newComment, author: userEmail }),
            });
            setNewComment("");
            fetchComments(selectedFileId);
        } catch (error) {
            console.error("Yorum gönderilirken hata:", error);
        }
    };

    return (
        <div className="space-y-6">
            {authorized ? (
                <>
                    {/* Dosya Yükleme */}
                    <Card>
                        <CardHeader>
                            <h3 className="text-lg font-semibold">Dosya Yükle</h3>
                        </CardHeader>
                        <CardContent>
                            <Input type="file" onChange={handleUpload} />
                        </CardContent>
                    </Card>

                    {/* Dosyalar */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {files.map((file) => (
                            <Card
                                key={file.id}
                                className="hover:shadow-lg transition cursor-pointer"
                                onClick={() => fetchComments(file.id)}
                            >
                                <CardHeader>
                                    <h4 className="font-semibold">{file.filename}</h4>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-gray-500">
                                        Yükleyen: {file.uploader}
                                    </p>

                                    {/* Tek gösterimlik medya */}
                                    {file.single_view && (
                                        <SingleViewMedia
                                            mediaUrl={file.url}
                                            userEmail={userEmail}
                                            onConsumed={() =>
                                                alert("Medya tek gösterimlik olarak kullanıldı ve artık erişilemez.")
                                            }
                                        />
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>

                    {/* Yorumlar */}
                    {selectedFileId && (
                        <Card>
                            <CardHeader>
                                <h3 className="text-lg font-semibold">Yorumlar</h3>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    {(comments[selectedFileId] || []).map((c, i) => (
                                        <div
                                            key={i}
                                            className="p-2 border rounded-md bg-gray-50 text-sm"
                                        >
                                            <span className="font-semibold">{c.author}:</span> {c.text}
                                        </div>
                                    ))}
                                </div>
                                <div className="flex gap-2">
                                    <Textarea
                                        value={newComment}
                                        onChange={(e) => setNewComment(e.target.value)}
                                        placeholder="Yorum yaz..."
                                    />
                                    <Button onClick={postComment}>Gönder</Button>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </>
            ) : (
                <p className="text-red-500 font-medium">
                    ⚠ Bu grup içeriğine erişim yetkiniz yok.
                </p>
            )}
        </div>
    );
};

export default GroupContent;


