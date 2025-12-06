import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useApi } from "../utils/api";
import { Card, CardContent } from "./ui/Card";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    CartesianGrid,
    ResponsiveContainer,
} from "recharts";

import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "./ui/Select";

export default function FileReport() {
    const { fileId } = useParams();
    const { apiFetch } = useApi();
    const [report, setReport] = useState(null);
    const [interval, setInterval] = useState("daily");

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

    const chartData = report.stats[interval].map((d) => ({
        date: new Date(d.period).toLocaleDateString(),
        views: d.count,
    }));

    return (
        <div className="p-6 space-y-6">
            <h2 className="text-2xl font-bold">📊 Rapor: {report.file}</h2>
            <p className="text-gray-600">Toplam görüntülenme: {report.total_views}</p>

            {/* Görünüm seçici */}
            <div className="w-48">
                <Select value={interval} onValueChange={setInterval}>
                    <SelectTrigger>
                        <SelectValue placeholder="Görünüm seç" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="daily">Günlük</SelectItem>
                        <SelectItem value="weekly">Haftalık</SelectItem>
                        <SelectItem value="monthly">Aylık</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Grafik */}
            <Card>
                <CardContent className="p-4">
                    <h3 className="font-semibold mb-2">📈 {interval.toUpperCase()} Görüntüleme</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" />
                            <YAxis allowDecimals={false} />
                            <Tooltip />
                            <Line type="monotone" dataKey="views" stroke="#2563eb" strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            {/* Görüntüleme log listesi */}
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
