// SecureFileViewer.jsx
import React, { useState, useEffect } from 'react';
import SingleViewMedia from './SingleViewMedia'; // Eski component
import SecureViewer from './SecureViewer'; // Yeni component
import { useParams } from 'react-router-dom';

const SecureFileViewer = () => {
    const [fileData, setFileData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { token } = useParams();

    useEffect(() => {
        const fetchFileData = async () => {
            if (!token) {
                setError("Geçersiz veya eksik token.");
                setLoading(false);
                return;
            }
            try {
                // API endpoint'ini güncelle
                const response = await fetch(`http://localhost:8001/api/share/${token}/`);

                if (response.headers.get('X-Security-Breach') === 'CAMERA_DETECTED') {
                    throw new Error('Kamera Güvenlik İhlali Tespit Edildi ve Engellendi.');
                }

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Dosya yüklenirken hata oluştu');
                }

                const data = await response.json();
                setFileData(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchFileData();
    }, [token]);

    if (loading) {
        return (
            <div style={{
                padding: '50px',
                textAlign: 'center',
                background: '#1a1a1a',
                color: 'white',
                borderRadius: '8px'
            }}>
                <div>Dosya yükleniyor...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{
                padding: '50px',
                textAlign: 'center',
                background: '#ff4444',
                color: 'white',
                borderRadius: '8px'
            }}>
                <h3>Hata</h3>
                <p>{error}</p>
            </div>
        );
    }

    if (!fileData) {
        return (
            <div style={{
                padding: '50px',
                textAlign: 'center',
                background: '#ffaa00',
                color: 'white',
                borderRadius: '8px'
            }}>
                <p>Dosya bulunamadı</p>
            </div>
        );
    }

    // Eski SingleViewMedia component'ini kullanmak için:
    // return (
    //     <SingleViewMedia
    //         secureMediaUrl={fileData.secure_media_url}
    //         userEmail={fileData.user_email}
    //         onConsumed={() => console.log('Content consumed')}
    //     />
    // );

    // Yeni SecureViewer component'ini kullanmak için:
    return (
        <SecureViewer
            file={{
                one_time_view: fileData.one_time_view,
                file_name: fileData.file_name,
                secure_media_url: fileData.secure_media_url
            }}
            user={{
                email: fileData.user_email,
                username: fileData.user_email?.split('@')[0] || 'Kullanıcı'
            }}
        >
            <div style={{ textAlign: 'center', padding: '20px' }}>
                <img
                    src={fileData.secure_media_url}
                    alt={fileData.file_name}
                    style={{
                        maxWidth: '100%',
                        maxHeight: '80vh',
                        borderRadius: '8px'
                    }}
                    onError={(e) => {
                        console.error('Resim yüklenemedi');
                        e.target.style.display = 'none';
                    }}
                />
            </div>
        </SecureViewer>
    );
};

export default SecureFileViewer;