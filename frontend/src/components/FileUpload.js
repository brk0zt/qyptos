import React, { useState } from 'react';
import { fileAPI } from '../services/api';
import { useMemory } from '../../../contexts/MemoryContext';

const FileUpload = ({ groupId }) => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [options, setOptions] = useState({
        one_time_view: false,
        view_duration: 'unlimited',
        watermark_enabled: true
    });

    const handleFileSelect = (e) => {
        setSelectedFile(e.target.files[0]);
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!selectedFile) return;

        setUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('one_time_view', options.one_time_view);
            formData.append('view_duration', options.view_duration);
            formData.append('watermark_enabled', options.watermark_enabled);

            const response = await fileAPI.uploadFile(groupId, formData);
            alert('Dosya başarıyla yüklendi!');
            setSelectedFile(null);

            // Formu resetle
            e.target.reset();
        } catch (error) {
            console.error('Dosya yüklenirken hata:', error);
            alert('Dosya yüklenemedi!');
        } finally {
            setUploading(false);
        }
    };

    const { trackActivity } = useMemory();

    const handleUploadComplete = (fileData) => {
        // Hafıza sistemine dosya yüklendiğini bildir
        trackActivity('file_upload', {
            file_id: fileData.id,
            file_name: fileData.name,
            file_type: fileData.type,
            file_size: fileData.size
        });
    };

    return (
        <div className="file-upload">
            <h3>Dosya Yükle</h3>
            <form onSubmit={handleUpload}>
                <input
                    type="file"
                    onChange={handleFileSelect}
                    disabled={uploading}
                    required
                />

                <div className="upload-options">
                    <label>
                        <input
                            type="checkbox"
                            checked={options.one_time_view}
                            onChange={(e) => setOptions({ ...options, one_time_view: e.target.checked })}
                        />
                        Tek seferlik görüntüleme
                    </label>

                    <label>
                        <input
                            type="checkbox"
                            checked={options.watermark_enabled}
                            onChange={(e) => setOptions({ ...options, watermark_enabled: e.target.checked })}
                        />
                        Filigran ekle
                    </label>

                    <select
                        value={options.view_duration}
                        onChange={(e) => setOptions({ ...options, view_duration: e.target.value })}
                    >
                        <option value="unlimited">Süresiz</option>
                        <option value="10s">10 saniye</option>
                        <option value="30s">30 saniye</option>
                        <option value="1m">1 dakika</option>
                        <option value="5m">5 dakika</option>
                        <option value="1h">1 saat</option>
                    </select>

                    <div className="upload-option-item">
                        <label htmlFor="canDownload" className="checkbox-label">
                            <input
                                type="checkbox"
                                id="canDownload"
                                checked={canDownload}
                                onChange={(e) => setCanDownload(e.target.checked)}
                            />
                            <i className={`fas ${canDownload ? 'fa-check-square' : 'fa-square'}`}></i>
                            Dosyanın İndirilmesine İzin Ver
                        </label>
                    </div>

                </div>

                <button type="submit" disabled={uploading || !selectedFile}>
                    {uploading ? 'Yükleniyor...' : 'Dosya Yükle'}
                </button>
            </form>
        </div>
    );
};

export default FileUpload;