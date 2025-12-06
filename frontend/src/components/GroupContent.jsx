import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardContent } from './ui/Card';
import { Input } from "./Input";
import { Button } from './ui/Button';
import { Textarea } from "./Textarea";
import SingleViewMedia from "./SingleViewMedia";
import { Label } from "./ui/Label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "./ui/Select";
import { useApi } from "../hooks/useApi"; // Yeni useApi hook'u
import { groupAPI, fileAPI, authAPI } from "../utils/api"; 

const GroupContent = ({ groupId }) => {
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
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // GroupContent.jsx - useEffect içinde
    useEffect(() => {
        const checkAuthAndFetchFiles = async () => {
            try {
                setLoading(true);

                // Demo mod kontrolü
                const token = localStorage.getItem('token');
                if (!token) {
                    setAuthorized(false);
                    setLoading(false);
                    return;
                }

                // Kullanıcı bilgisini al
                const userResponse = await authAPI.checkAuth();
                setUser(userResponse.data);

                if (groupId) {
                    const authResponse = await groupAPI.checkGroupAuth(groupId);
                    if (authResponse.data.authorized) {
                        setAuthorized(true);
                        const filesResponse = await groupAPI.getGroupFiles(groupId);
                        setFiles(filesResponse.data);
                    } else {
                        setAuthorized(false);
                    }
                }
            } catch (error) {
                console.error("Auth veya dosya yükleme hatası:", error);
                setAuthorized(false);

                // Demo data göster
                if (error.response?.status === 401 || !localStorage.getItem('token')) {
                    const demoFiles = [
                        { id: 1, filename: "demo-file-1.jpg", uploaded_by: "Demo User", one_time_view: false },
                        { id: 2, filename: "demo-file-2.png", uploaded_by: "Demo User", one_time_view: true }
                    ];
                    setFiles(demoFiles);
                    setAuthorized(true);
                }
            } finally {
                setLoading(false);
            }
        };

        if (groupId) {
            checkAuthAndFetchFiles();
        }
    }, [groupId]);

    const handleFileUpload = async (file) => {

        if (!authorized || !groupId || !file) {
            setMessage("❌ Lütfen dosya seçin ve yetkinizi kontrol edin.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("one_time_view", oneTime);
        formData.append("view_duration", duration);
        formData.append("watermark_enabled", watermark);
        formData.append('can_download', canDownload);

        try {
            const response = await fileAPI.uploadFile(groupId, formData);
            setMessage(`✅ Dosya yüklendi!`);

            // Dosya listesini güncelle
            const filesResponse = await groupAPI.getGroupFiles(groupId);
            setFiles(filesResponse.data);
            setFile(null);
        } catch (error) {
            console.error("Dosya yükleme hatası:", error);
            setMessage("❌ Dosya yüklenirken hata oluştu.");
        }
    };

    const fetchComments = async (fileId) => {
        setSelectedFileId(fileId);
        try {
            const response = await fileAPI.getFileComments(fileId);
            setComments((prev) => ({ ...prev, [fileId]: response.data }));
        } catch (error) {
            console.error("Yorumlar yüklenirken hata:", error);
        }
    };

    const postComment = async () => {
        if (!authorized || !selectedFileId || !newComment.trim()) return;
        try {
            await fileAPI.addComment(selectedFileId, newComment);
            setNewComment("");
            fetchComments(selectedFileId); // Yorumları yenile
        } catch (error) {
            console.error("Yorum gönderilirken hata:", error);
        }
    };

    if (loading) {
        return <div>Yükleniyor...</div>;
    }

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
                            <Input
                                type="file"
                                onChange={(e) => setFile(e.target.files[0])}
                            />

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

                            <Button onClick={handleFileUpload} disabled={!file}>
                                Yükle
                            </Button>
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
                                        Yükleyen: {file.uploaded_by}
                                    </p>

                                    {/* Tek gösterimlik medya */}
                                    {file.one_time_view && !file.has_been_viewed && (
                                        <SingleViewMedia
                                            mediaUrl={file.view_url}
                                            userEmail={user?.email}
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
                                    {(comments[selectedFileId] || []).map((comment, index) => (
                                        <div
                                            key={index}
                                            className="p-2 border rounded-md bg-gray-50 text-sm"
                                        >
                                            <span className="font-semibold">{comment.author}:</span> {comment.text}
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
                    ⚠ Bu grup içeriğine erişim yetkiniz yok veya grup bulunamadı.
                </p>
            )}
        </div>
    );
};

export default GroupContent;