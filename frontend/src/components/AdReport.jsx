import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent } from "./ui/Card";
import { Button } from "./ui/Button";

export default function AdReport() {
    const { adId } = useParams();
    const [report, setReport] = useState(null);
    const [interval, setInterval] = useState("daily");

    const handleDownload = (type) => {
        const url = `http://127.0.0.1:8001/ads/${adId}/report/${type}/`;
        window.open(url, "_blank");
    };

    useEffect(() => {
        const loadReport = async () => {
            try {
                const token = localStorage.getItem('token');
                const res = await fetch(`http://127.0.0.1:8001/ads/${adId}/report/`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                });
                if (res.ok) {
                    const data = await res.json();
                    setReport(data);
                }
            } catch (error) {
                console.error("Rapor yüklenirken hata:", error);
            }
        };
        loadReport();
    }, [adId]);

    if (!report) return <div className="p-6"><p>Yükleniyor...</p></div>;

    return (
        <div className="p-6 space-y-6">
            <h2 className="text-2xl font-bold">📊 Reklam Raporu: {report.ad}</h2>

            {/* Basit istatistikler - grafik olmadan */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="p-4 text-center">
                        <h3 className="text-lg font-bold text-blue-600">{report.views || 0}</h3>
                        <p>Toplam Görüntüleme</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4 text-center">
                        <h3 className="text-lg font-bold text-green-600">{report.clicks || 0}</h3>
                        <p>Toplam Tıklama</p>
                    </CardContent>
                </Card>
            </div>

            {/* İndirme butonları */}
            <div className="flex gap-2">
                <Button onClick={() => handleDownload("csv")}>⬇️ CSV indir</Button>
                <Button onClick={() => handleDownload("pdf")}>⬇️ PDF indir</Button>
            </div>

            {/* Detaylı log listesi */}
            <div className="space-y-4">
                <h3 className="font-semibold text-lg">📑 Son Etkileşimler</h3>
                {report.logs && report.logs.map((log, idx) => (
                    <Card key={idx}>
                        <CardContent className="p-4">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p><b>Kullanıcı:</b> {log.user || 'Anonim'}</p>
                                    <p><b>Olay:</b>
                                        <span className={`ml-2 px-2 py-1 rounded ${log.event_type === "view" ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                                            }`}>
                                            {log.event_type === "view" ? "👀 Görüntüleme" : "🖱️ Tıklama"}
                                        </span>
                                    </p>
                                </div>
                                <p className="text-gray-500 text-sm">
                                    {new Date(log.created_at).toLocaleString()}
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
}
