import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardContent } from '../ui/Card';

//import { Input } from "@/components/ui/input";
import { Button } from './ui/Button';

const DeviceFileAccess = ({ apiBase, userEmail }) => {
    const [file, setFile] = useState(null);
    const [message, setMessage] = useState("");
    const [authorized, setAuthorized] = useState(false);

    useEffect(() => {
        // Backend API üzerinden kullanıcı yetkisini kontrol et
        fetch(`${apiBase}/device-files/check-auth/?user=${userEmail}`)
            .then((res) => res.json())
            .then((data) => setAuthorized(data.authorized))
            .catch(() => setAuthorized(false));
    }, [apiBase, userEmail]);

    const handleUpload = async () => {
        if (!file || !authorized) return;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("owner", userEmail);

        const res = await fetch(`${apiBase}/device-files/`, {
            method: "POST",
            body: formData,
        });

        if (res.ok) {
            setMessage("✅ Dosya başarıyla yüklendi.");
            setFile(null);
        } else {
            setMessage("❌ Dosya yüklenirken hata oluştu.");
        }
    };

    return (
        <Card>
            <CardHeader>
                <h3 className="text-lg font-semibold">Cihaz Anahtarı Tabanlı Dosya</h3>
            </CardHeader>
            <CardContent className="space-y-4">
                {authorized ? (
                    <>
                        <Input type="file" onChange={(e) => setFile(e.target.files[0])} />
                        <Button onClick={handleUpload} disabled={!file}>
                            Yükle
                        </Button>
                        {message && <div className="mt-2 text-sm">{message}</div>}
                    </>
                ) : (
                    <p className="text-red-500 font-medium">
                        ⚠ Bu modüle erişim yetkiniz yok.
                    </p>
                )}
            </CardContent>
        </Card>
    );
};

export default DeviceFileAccess;


