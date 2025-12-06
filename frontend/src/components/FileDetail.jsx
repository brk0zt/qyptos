import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useApi } from '../hooks/useApi';
import { Card, CardContent } from "./ui/Card";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";
import { Download } from "lucide-react";

export default function FileDetail() {
    const { fileId } = useParams();
    const { apiFetch } = useApi();
    const [file, setFile] = useState(null);
    const [comments, setComments] = useState([]);
    const [newComment, setNewComment] = useState("");
    const [expired, setExpired] = useState(false);

    const handleDownload = () => {
        window.open(`http://127.0.0.1:8001/groups/files/${fileId}/download/`, "_blank");
    };



    useEffect(() => {
        const loadFile = async () => {
            const res = await apiFetch(`http://127.0.0.1:8001/groups/files/${fileId}/`);
            if (res.ok) {
                const data = await res.json();
                setFile(data.file);
                setComments(data.comments);
            }
        };
        loadFile();
    }, [fileId]);

    const handleAddComment = async () => {
        const res = await apiFetch(`http://127.0.0.1:8001/groups/files/${fileId}/`, {
            method: "POST",
            body: JSON.stringify({ text: newComment }),
        });
        if (res.ok) {
            const data = await res.json();
            setComments((prev) => [data, ...prev]);
            setNewComment("");
        }
    };

    if (!file) return <p>Yükleniyor...</p>;

    useEffect(() => {
        const handleKey = (e) => {
            if (e.key === "PrintScreen") {
                alert("⚠️ Ekran görüntüsü almak yasak!");
                e.preventDefault();
            }
        };

        const handleContext = (e) => {
            e.preventDefault();
            alert("⚠️ Sağ tık devre dışı bırakıldı!");
        };

        window.addEventListener("keydown", handleKey);
        window.addEventListener("contextmenu", handleContext);

        return () => {
            window.removeEventListener("keydown", handleKey);
            window.removeEventListener("contextmenu", handleContext);
        };
    }, []);


    useEffect(() => {
        if (file && file.one_time_view && file.view_url) {
            let timeout = null;

            const duration = file.view_duration;

            const durationMap = {
                "10s": 10000,
                "30s": 30000,
                "1m": 60000,
                "5m": 300000,
                "1h": 3600000,
            };

            if (duration in durationMap) {
                timeout = setTimeout(() => setExpired(true), durationMap[duration]);
            } else if (duration === "video") {
                // Eğer video ise → video elementinden süre al
                const video = document.querySelector("#secureVideo");
                if (video) {
                    video.onloadedmetadata = () => {
                        timeout = setTimeout(() => setExpired(true), video.duration * 1000);
                    };
                }
            } else if (duration === "unlimited") {
                // süresiz → timeout yok
            }

            return () => {
                if (timeout) clearTimeout(timeout);
            };
        }
    }, [file]);


    return (
        <div className="p-6">
            {expired ? (
                <div className="p-10 text-center text-red-600 font-bold text-xl">
                    ⛔ Bu dosyanın görüntüleme süresi doldu.
                </div>
            ) : (
                file.one_time_view &&
                file.view_url && (
                    <div className="relative border rounded overflow-hidden">
                        {file.filename.endsWith(".mp4") ? (
                            <video
                                id="secureVideo"
                                src={file.view_url}
                                controls
                                className="w-full h-96"
                            />
                        ) : (
                            <iframe
                                src={file.view_url}
                                className="w-full h-96"
                                title="Secure Viewer"
                            ></iframe>
                        )}

                        {/* Dinamik Watermark */}
                            {file.watermark && file.watermark_enabled && (
                                <div className="absolute inset-0 flex items-center justify-center opacity-30 pointer-events-none">
                                    <span className="text-3xl font-bold text-gray-700 rotate-45 text-center">
                                        {file.watermark.username.toUpperCase()}
                                        <br />
                                        {new Date(file.watermark.timestamp).toLocaleString()}
                                    </span>
                                </div>
                            )}
                    </div>
                )
            )}
        </div>
    );
}