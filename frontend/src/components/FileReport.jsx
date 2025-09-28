import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useApi } from "../utils/api";
import { Card, CardContent } from "./ui/Card";

export default function FileReport() {
    const { fileId } = useParams();
    const { apiFetch } = useApi();
    const [report, setReport] = useState(null);

    useEffect(() => {
        const loadReport = async () => {
            const res = await apiFetch(`http://127.0.0.1:8001/groups/files/${fileId}/report/`);
            if (res.ok) {
                const data = await res.json();
                setReport(data);
            }
        };
        loadReport();
    }, [fileId]);

    if (!report) return <p>Yükleniyor...</p>;

    return (
        <div className="p-6 space-y-4">
            <h2 className="text-2xl font-bold">📊 Rapor: {report.file}</h2>
            <p className="text-gray-600">Toplam görüntülenme: {report.total_views}</p>

            <div className="space-y-2">
                {report.logs.map((log, idx) => (
                    <Card key={idx}>
                        <CardContent>
                            <p><b>Kullanıcı:</b> {log.user}</p>
                            <p className="text-gray-500 text-sm">
                                {new Date(log.viewed_at).toLocaleString()}
                            </p>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
}
