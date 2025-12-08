// SingleViewMedia.jsx - DÜZELTİLMİŞ
import React, { useEffect, useState, useRef, useCallback } from "react";

const SingleViewMedia = ({ secureMediaUrl, userEmail, onConsumed, onReady }) => {
    const canvasRef = useRef(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSecurityAlert, setIsSecurityAlert] = useState(false);
    const [isLocallyConsumed, setIsLocallyConsumed] = useState(Boolean(isConsumedByBackend));

    // Tekrarlı tetiklemeleri engellemek için basit flag/debounce
    const triggerAggressiveAction = useCallback((reason) => {

        /*
        if (isSecurityAlert || isLocallyConsumed) return;
        console.warn(`[AGRESİF GÜVENLİK İHLALİ] Tespit Edilen İhlal: ${reason}`);
        setIsSecurityAlert(true);
        setIsLocallyConsumed(true);

        // Backend'e bildir (örnek endpoint - kendi backend'ine göre değiştir)
        try {
            fetch('/api/security/consume/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ reason, user: userEmail, consumed: true })
            }).catch(err => console.warn("Backend consume bildirimi başarısız:", err));
        } catch (e) {
            console.warn("Consume bildirimi atılamadı:", e);
        }

        if (onConsumed) {
            try { onConsumed(); } catch (e) { console.warn("onConsumed call failed:", e); }
        }
        */
    }, [isSecurityAlert, isLocallyConsumed, userEmail, onConsumed]);

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Klavye (PrtScn / DevTools) koruması
    useEffect(() => {
        const handleKeyDown = (e) => {
            // Modern tarayıcılarda key ve keyCode kontrolü
            const key = e.key || '';
            const code = e.keyCode || e.which || 0;

            // PrintScreen (44), F12 (123) veya Ctrl+Shift+I/J/C
            if (code === 44 || code === 123 || (e.ctrlKey && e.shiftKey && [73, 74, 67].includes(code))) {
                e.preventDefault();
                e.stopPropagation();
                triggerAggressiveAction(code === 44 ? "Ekran Görüntüsü Tuşu (PrtScn)" : "Geliştirici Araçları/ F12 veya Kısayol");
            }
        };

        // capture fazında ekle (mümkün olan en hızlı tepki)
        document.addEventListener('keydown', handleKeyDown, true);

        return () => {
            document.removeEventListener('keydown', handleKeyDown, true);
        };
    }, [triggerAggressiveAction]);

    // Canvas'a resmi güvenli şekilde çekme + tüketim bildirimi
    useEffect(() => {
        if (isLocallyConsumed || !secureMediaUrl) {
            setIsLoading(false);
            return;
        }

        const canvas = canvasRef.current;
        if (!canvas) {
            setIsLoading(false);
            return;
        }
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            setIsLoading(false);
            return;
        }

        let cancelled = false;
        const img = new Image();
        img.crossOrigin = 'anonymous';

        img.onload = () => {
            if (cancelled) return;
            if (onReady) onReady();
            // Basit ölçekleme: canvas boyutunu resme göre ayarla (gerekirse responsive geliştir)
            const maxWidth = Math.min(window.innerWidth * 0.9, img.width);
            const scale = maxWidth / img.width;
            canvas.width = img.width * scale;
            canvas.height = img.height * scale;
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            setIsLoading(false);

            // Backend'e "görüntülendi/consume" bildirimi
            setIsLocallyConsumed(true);
            try {
                fetch('/api/security/consume/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ consumed: true, user: userEmail, url: secureMediaUrl })
                }).catch(err => console.warn("consume bildirimi başarısız:", err));
            } catch (e) {
                console.warn("consume bildirimi atılamadı:", e);
            }

            if (onConsumed) {
                try { onConsumed(); } catch (e) { console.warn("onConsumed hata:", e); }
            }
        };

        img.onerror = () => {
            if (cancelled) return;
            console.error("Resim yüklenemedi.");
            setIsLoading(false);
            setIsLocallyConsumed(true);
        };

        img.src = secureMediaUrl;

        return () => {
            cancelled = true;
        };
    }, [secureMediaUrl, isLocallyConsumed, onConsumed, userEmail]);

    // Kamera/monitoring stop sinyali - component unmount olduğunda
    useEffect(() => {
        return () => {
            console.log("📸 Kamera stop cleanup tetiklendi");
            fetch('/api/security/camera/stop/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ user: userEmail })
            })
                .then(res => console.log("Kamera stop status:", res.status))
                .catch(error => console.error("Kamera stop hatası:", error));
        };
    }, [userEmail]);

    if (isSecurityAlert || isLocallyConsumed) {
        return (
            <div
                style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    backgroundColor: 'rgba(0, 0, 0, 0.98)',
                    color: 'white',
                    zIndex: 99999,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    fontSize: '24px',
                    textAlign: 'center'
                }}
            >
                <div style={{ fontSize: '72px', color: 'red', marginBottom: '20px' }}>🚫</div>
                <p>{isSecurityAlert ? "Güvenlik İhlali Tespit Edildi." : "Bu medya artık görüntülenemez."}</p>
                <p style={{ fontSize: '16px', color: '#ccc' }}>İçeriğe erişiminiz bu oturum için engellenmiştir.</p>
            </div>
        );
    }

    return (
        <div className="relative inline-block secure-content" style={{ userSelect: 'none', pointerEvents: 'auto' }}>
            {isLoading && (
                <div className="flex justify-center items-center h-40 w-full text-gray-500">
                    Görüntü yükleniyor...
                </div>
            )}
            <canvas
                ref={canvasRef}
                className="protected-canvas"
                style={{
                    display: isLoading ? 'none' : 'block',
                    transform: 'translateZ(0)',
                    willChange: 'transform',
                    filter: 'blur(0.0001px)'
                }}
            />
        </div>
    );
};

export default SingleViewMedia;
