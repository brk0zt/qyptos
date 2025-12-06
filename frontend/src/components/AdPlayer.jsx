import React, { useEffect, useState } from "react";
import { useApi } from '../hooks/useApi';
import { Card, CardContent } from "./ui/Card";
import { Button } from "./ui/Button";

export default function AdPlayer() {
    const { apiFetch } = useApi();
    const [ad, setAd] = useState(null);
    const [countdown, setCountdown] = useState(0);

    // Reklam çekme
    const loadAd = async () => {
        const res = await apiFetch("http://127.0.0.1:8001/ads/");
        if (res.ok) {
            const data = await res.json();
            setAd(data);
            setCountdown(data.duration); // süre başlat
        } else {
            setAd(null);
        }
    };

    useEffect(() => {
        loadAd();
    }, []);

    // Geri sayım
    useEffect(() => {
        if (countdown > 0) {
            const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [countdown]);

    if (!ad) {
        return <p className="text-gray-500">Şu anda reklam bulunmuyor.</p>;
    }

    const isVideo = ad.media.endsWith(".mp4") || ad.media.endsWith(".webm");
    const isImage = ad.media.endsWith(".jpg") || ad.media.endsWith(".jpeg") || ad.media.endsWith(".png");

    const handleClick = async () => {
        await apiFetch(`http://127.0.0.1:8001/ads/${ad.id}/click/`, {
            method: "POST",
        });
        window.open(ad.link, "_blank", "noopener,noreferrer");
    };

    return (
        <Card className="max-w-lg mx-auto shadow-lg">
            <CardContent className="p-4 space-y-3 text-center">
                <h3 className="font-bold text-lg">{ad.title}</h3>

                {/* Reklam içeriği */}
                {isVideo && (
                    <video
                        src={ad.media}
                        autoPlay
                        controls={false}
                        muted
                        className="w-full rounded"
                    />
                )}
                {isImage && (
                    <img src={ad.media} alt={ad.title} className="w-full rounded" />
                )}

                {/* Geri sayım */}
                {countdown > 0 ? (
                    <p className="text-sm text-gray-600">
                        Reklam {countdown} saniye sonra geçilebilir
                    </p>
                ) : (
                    <Button asChild className="mt-2">
                        <a href={ad.link} target="_blank" rel="noopener noreferrer">
                            Reklama Git →
                        </a>
                    </Button>
                )}
            </CardContent>
        </Card>
    );
}


