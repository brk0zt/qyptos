import React, { useState, useEffect } from "react";
// Bu import'ların, Card ve Button dosyaların ile aynı klasörde olması gerekiyor
import { Card, CardHeader, CardContent } from './ui/Card';
import { Button } from './ui/Button';

const AdPlayer = ({ apiBase, userEmail }) => {
    const [currentAd, setCurrentAd] = useState(null);
    const [showSkip, setShowSkip] = useState(false);

    useEffect(() => {
        // Mock API call to get ads
        const fetchAds = async () => {
            const res = await fetch(`${apiBase}/ads/?user=${userEmail}`);
            const data = await res.json();
            if (data.ads && data.ads.length > 0) {
                setCurrentAd(data.ads[0]);
                // Display the "Skip" button after 5 seconds
                setTimeout(() => {
                    setShowSkip(true);
                }, 5000);
            }
        };
        fetchAds();
    }, [apiBase, userEmail]);

    // Oynatıcı bileşeni
    return (
        <div className="flex flex-col items-center justify-center p-6 space-y-4">
            {currentAd ? (
                <Card className="w-full max-w-2xl">
                    <CardHeader>
                        <h3 className="text-lg font-semibold">
                            Oynatılıyor: {currentAd.title}
                        </h3>
                    </CardHeader>
                    <CardContent className="relative">
                        <div className="absolute top-2 left-2 text-white text-xs font-bold z-10 pointer-events-none select-none opacity-60">
                            {userEmail}
                        </div>
                        <video
                            src={currentAd.videoUrl}
                            controls
                            autoPlay
                            className="w-full rounded-lg shadow-md"
                            onClick={() => alert("⚠ Ekran kaydı veya PrintScreen yasaktır!")}
                        />
                        {showSkip && (
                            <div className="mt-4">
                                <Button onClick={() => setCurrentAd(null)}>Geç</Button>
                            </div>
                        )}
                    </CardContent>
                </Card>
            ) : (
                <p className="text-center font-medium">Reklam yok veya oynatma bitti.</p>
            )}
        </div>
    );
};

export default AdPlayer;

