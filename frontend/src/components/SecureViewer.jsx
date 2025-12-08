// SecureViewer.jsx - DÜZELTİLMİŞ
import React, { useEffect, useRef, useState } from "react";

const SecureViewer = ({ file, children, user, isMediaReady = false }) => {
    const [securityBreach, setSecurityBreach] = useState(false);
    const [debugInfo, setDebugInfo] = useState("Başlatılıyor...");
    const [isReady, setIsReady] = useState(false);
    const containerRef = useRef(null);
    const [isActive, setIsActive] = useState(false);

    // Basit state: sayacın zaman penceresi içinde resetlenmesi
    const violationStateRef = useRef({
        count: 0,
        lastTimestamps: [] // UNIX ms
    });
    const MAX_VIOLATIONS = 2;
    const WINDOW_MS = 5000; // aynı 5s içindeki ihlaller sayılacak

    useEffect(() => {
        const startupTimer = setTimeout(() => {
            setIsReady(true);
            setDebugInfo("✅ Güvenlik Sistemi Hazırlandı ve Kontroller Başlatıldı.");
        }, 300);
        return () => clearTimeout(startupTimer);
    }, []);

    useEffect(() => {
        if (isMediaReady) {
            setIsActive(true);
        }
    }, [isMediaReady]);

    useEffect(() => {
        if (!file?.one_time_view) {
            setDebugInfo("❌ one_time_view: false - Koruma GEREKSIZ");
            return;
        }

        setDebugInfo("✅ Gelişmiş Koruma AKTİF");

        
        const addViolation = (reason) => {
            const now = Date.now();
            const state = violationStateRef.current;
            // temizle eski timestamp'leri
            state.lastTimestamps = state.lastTimestamps.filter(ts => now - ts <= WINDOW_MS);
            state.lastTimestamps.push(now);
            state.count = state.lastTimestamps.length;
            setDebugInfo(`🚨 İhlal ${state.count}/${MAX_VIOLATIONS}: ${reason}`);

            if (state.count >= MAX_VIOLATIONS) {
                // kalıcı engelleme
                /*
                setSecurityBreach(true);
                setDebugInfo("🚨 MAKSIMUM IHLAL - Icerik engellendi!");
                */
            }
        };

        const detectScreenshotAttempt = (e) => {
            // sadece hazırsa işlem yap
            if (!isReady) return;

            const code = e.keyCode || e.which || 0;
            const key = e.key || '';

            // PrintScreen, F12, Ctrl+Shift+I/J/C
            const isPrint = code === 44 || key === 'PrintScreen' || key === 'Snapshot';
            const isF12 = code === 123 || key === 'F12';
            const isDevShortcut = (e.ctrlKey && e.shiftKey && ['I', 'J', 'C'].includes((key || '').toUpperCase())) ||
                (e.ctrlKey && e.shiftKey && [73, 74, 67].includes(code));

            if (isPrint || isF12 || isDevShortcut) {
               // e.preventDefault();
                // e.stopPropagation();
                console.log(`🚨 EKRAN GORUNTUSU DENEMESI: ${key || code}`);
                // overlay yerine controlled state
               // addViolation(isPrint ? "PrtScn" : isF12 ? "F12" : "DevTools Kısayolu");
            }
        };

        // Pencere odak kaybı: sadece arka plan/başka pencereye geçiş gerçek bir ihlal sayılmalı
        let blurTimer = null;
        const handleWindowBlur = () => {
            if (!isReady) return;
            /*
            // kısa odak kayıplarını yoksay (ör: 300ms altındaki)
            if (blurTimer) clearTimeout(blurTimer);
            blurTimer = setTimeout(() => {
                /* addViolation("Pencere Odağı Kaybı");
               
        }, 400);
            */
            console.log("Odak kaybı (Blur) engellendi."); // Sadece log bas
        };

        const handleWindowFocus = () => {
            if (blurTimer) {
                clearTimeout(blurTimer);
                blurTimer = null;
            }
        };

        const handleVisibilityChange = () => {
            if (!isReady) return;
            if (document.hidden) {
               /* addViolation("Sayfa Gizlendi/Arka Plana Alındı");
               */
                console.log("Sekme değiştirme (Visibility) engellendi."); // Sadece log bas
            }
        };

        const handleContextMenu = (e) => {
            // sağ tık açılmasını engelle - bu tek başına ihlal sayılmaz, ama logla
            e.preventDefault();
            e.stopPropagation();
            setDebugInfo("⚠️ Sağ tık engellendi");
        };

        const eventOptions = { capture: true, passive: false };

        document.addEventListener('keydown', detectScreenshotAttempt, eventOptions);
        document.addEventListener('keyup', detectScreenshotAttempt, eventOptions);
        window.addEventListener('blur', handleWindowBlur);
        window.addEventListener('focus', handleWindowFocus);
        document.addEventListener('visibilitychange', handleVisibilityChange);
        document.addEventListener('contextmenu', handleContextMenu, true);

        return () => {
            document.removeEventListener('keydown', detectScreenshotAttempt, eventOptions);
            document.removeEventListener('keyup', detectScreenshotAttempt, eventOptions);
            window.removeEventListener('blur', handleWindowBlur);
            window.removeEventListener('focus', handleWindowFocus);
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            document.removeEventListener('contextmenu', handleContextMenu, true);
            if (blurTimer) clearTimeout(blurTimer);
        };
    }, [file?.one_time_view, isActive]);

    if (securityBreach) {
        return (
            <div style={{
                width: '100%',
                height: '400px',
                background: 'linear-gradient(45deg, #000, #222)',
                color: '#ff4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                borderRadius: '8px',
                border: '3px solid #ff4444',
                textAlign: 'center',
                padding: '20px'
            }}>
                <div style={{ fontSize: '48px', marginBottom: '20px' }}>🚫</div>
                <h2 style={{ margin: '0 0 15px 0' }}>GÜVENLİK İHLALİ</h2>
                <p style={{ margin: '0 0 10px 0' }}>Bu içerik güvenlik nedeniyle engellendi.</p>
                <p style={{ margin: 0, fontSize: '14px', opacity: 0.8 }}>{debugInfo}</p>
            </div>
        );
    }

    return (
        <div
            ref={containerRef}
            className={`secure-content ${securityBreach ? 'security-breach-active' : ''}`}
            style={{
                position: 'relative',
                border: file?.one_time_view ? '3px solid #ff4444' : 'none',
                borderRadius: '8px',
                overflow: 'hidden',
                background: file?.one_time_view ? '#1a1a1a' : 'transparent',
                padding: file?.one_time_view ? '10px' : '0',
                userSelect: 'none'
            }}
        >
            {process.env.NODE_ENV === 'development' && (
                <div style={{
                    position: 'absolute',
                    top: '5px',
                    left: '5px',
                    background: 'rgba(0,0,0,0.8)',
                    color: '#00ff00',
                    padding: '5px',
                    borderRadius: '3px',
                    fontSize: '10px',
                    zIndex: 10000,
                    fontFamily: 'monospace'
                }}>
                    🛡️ {debugInfo}
                </div>
            )}

            {children}

            {file?.one_time_view && (
                <>
                    <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        background: `repeating-linear-gradient(45deg, rgba(255,0,0,0.05), rgba(255,0,0,0.05) 10px, rgba(0,0,255,0.03) 10px, rgba(0,0,255,0.03) 20px)`,
                        pointerEvents: 'none',
                        zIndex: 9998
                    }} />

                    <div style={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%) rotate(-45deg)',
                        color: 'rgba(255,255,255,0.12)',
                        fontSize: '48px',
                        fontWeight: 'bold',
                        whiteSpace: 'nowrap',
                        pointerEvents: 'none',
                        zIndex: 9997,
                        textAlign: 'center'
                    }}>
                        {user?.username || 'Kullanici'} | {user?.email || ''} | {new Date().toLocaleDateString('tr-TR')}
                    </div>

                    <div style={{
                        position: 'absolute',
                        bottom: '10px',
                        right: '10px',
                        color: 'rgba(255,255,255,0.6)',
                        fontSize: '12px',
                        background: 'rgba(0,0,0,0.5)',
                        padding: '5px 10px',
                        borderRadius: '3px',
                        pointerEvents: 'none',
                        zIndex: 9999
                    }}>
                        {user?.username || 'Kullanici'} | {new Date().toLocaleString('tr-TR')}
                    </div>
                </>
            )}
        </div>
    );
};

export default SecureViewer;
