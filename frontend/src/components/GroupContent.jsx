import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardContent } from './ui/Card';
import { Input } from "./Input";
import { Button } from './ui/Button';
import { Textarea } from "./Textarea";
import SingleViewMedia from "./SingleViewMedia";
import { Label } from "./ui/Label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "./ui/Select";
import useApi from "./useApi";

const GroupContent = ({ groupId, apiBase, userEmail }) => {
    const [authorized, setAuthorized] = useState(false);
    const [files, setFiles] = useState([]);
    const [comments, setComments] = useState({});
    const [newComment, setNewComment] = useState("");
    const [selectedFileId, setSelectedFileId] = useState(null);
    const [file, setFile] = useState(null);
    const [oneTime, setOneTime] = useState(false);
    const [duration, setDuration] = useState("unlimited");
    const [watermark, setWatermark] = useState(true);
    const [message, setMessage] = useState("");
    const { apiFetch } = useApi();

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

    const handleFileUpload = async (e) => {
        if (!authorized) return;
        const uploadedFile = e.target.files[0];
        if (!uploadedFile) return;

        const formData = new FormData();
        formData.append("file", uploadedFile);
        formData.append("one_time_view", oneTime);
        formData.append("view_duration", duration);
        formData.append("watermark_enabled", watermark);

        try {
            const res = await apiFetch(`${apiBase}/groups/${groupId}/upload/`, {
                method: "POST",
                body: formData,
            });

            if (res.ok) {
                const data = await res.json();
                setMessage(`✅ Dosya yüklendi (tek seferlik: ${data.one_time_view}, süre: ${data.view_duration}, watermark: ${data.watermark_enabled})`);
                setFile(null);

                // Dosya listesini güncelle
                const updated = await fetch(`${apiBase}/groups/${groupId}/files/`).then((r) =>
                    r.json()
                );
                setFiles(updated);
            } else {
                setMessage("❌ Dosya yüklenemedi.");
            }
        } catch (error) {
            console.error("Dosya yükleme hatası:", error);
            setMessage("❌ Dosya yüklenirken hata oluştu.");
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
                        <CardContent className="space-y-4">
                            <Input type="file" onChange={(e) => setFile(e.target.files[0])} />

                            <div className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    id="oneTime"
                                    checked={oneTime}
                                    onChange={(e) => setOneTime(e.target.checked)}
                                />
                                <Label htmlFor="oneTime">Tek seferlik görüntüleme</Label>
                            </div>

                            <div>
                                <Label className="block mb-1">⏳ Görüntüleme Süresi</Label>
                                <Select value={duration} onValueChange={setDuration}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Süre seçin" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="10s">10 saniye</SelectItem>
                                        <SelectItem value="30s">30 saniye</SelectItem>
                                        <SelectItem value="1m">1 dakika</SelectItem>
                                        <SelectItem value="5m">5 dakika</SelectItem>
                                        <SelectItem value="1h">1 saat</SelectItem>
                                        <SelectItem value="video">Video süresi</SelectItem>
                                        <SelectItem value="unlimited">Süresiz</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    id="watermark"
                                    checked={watermark}
                                    onChange={(e) => setWatermark(e.target.checked)}
                                />
                                <Label htmlFor="watermark">Watermark ekle</Label>
                            </div>

                            <Button onClick={handleFileUpload}>Yükle</Button>
                            {message && <p className="text-sm">{message}</p>}
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
                                        Yükleyen: {file.uploaded_by?.username}
                                    </p>

                                    {/* Tek gösterimlik medya */}
                                    {file.one_time_view && !file.has_been_viewed && (
                                        <SingleViewMedia
                                            mediaUrl={file.view_url}
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