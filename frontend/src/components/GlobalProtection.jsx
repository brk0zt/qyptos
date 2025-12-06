// GlobalProtection.jsx - ANINDA BLACKOUT TEKNİĞİ
import React, { useEffect, useState, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

const GlobalProtection = () => {
    const location = useLocation();
    // Güvenlik uyarısı durumunu tutar
    const [isSecurityAlert, setIsSecurityAlert] = useState(false);

    // Kodu daha temiz hale getirmek için aksiyonu bir fonksiyona ayırıyoruz
    const triggerAggressiveAction = useCallback((reason) => {
        if (!isSecurityAlert) {
            console.warn(`[AGRESİF GÜVENLİK İHLALİ] Tespit Edilen İhlal: ${reason}`);
            // isSecurityAlert'ı anında TRUE yaparak, aşağıdaki if bloğunu tetikleriz.
            setIsSecurityAlert(true);
            // Bu state değişikliği, bileşenin yeniden render edilmesini ve 
            // tüm ekranı kaplayan siyah katmanın (Blackout) anında DOM'a eklenmesini sağlar.
        }
    }, [isSecurityAlert]);

    useEffect(() => {
        const path = location.pathname;

        // Bu rotalarda güvenlik uyarısı SIFIRLANMALIDIR
        // `path.startsWith` kullanmak daha güvenlidir, çünkü `/dashboard/settings` gibi alt rotaları da yakalar.
        const shouldResetAlert = path.startsWith('/login') ||
            path.startsWith('/register') ||
            path.startsWith('/dashboard') ||
            path === '/';

        if (shouldResetAlert && isSecurityAlert) {
            // Eğer güvenli bir rotadaysak VE uyarı aktifse, uyarısını KESİNLİKLE kapat.
            // setIisSecurityAlert'ın [isSecurityAlert] bağımlılığı sayesinde, 
            // sadece true ise sıfırlamaya çalışır, bu da sonsuz döngüyü engeller.
            setIsSecurityAlert(false);
            console.log("[SECURITY] Global uyarı durumu güvenli rotada sıfırlandı.");
        }

        let checkDevTools = null;
        let handleVisibilityChange = null;

        const startProtectionTimer = setTimeout(() => {

            // Geliştirici Araçları Kontrolü
            checkDevTools = setInterval(() => {
                // ... (Boyut ve Debugger kontrolleri aynı kalacak)
                if (window.outerWidth - window.innerWidth > 100 || window.outerHeight - window.innerHeight > 100) {
                    triggerAggressiveAction("DevTools: Boyut Farkı");
                }
                if (window.devToolsExtension || /./.test(() => { debugger; })) {
                    triggerAggressiveAction("DevTools: Debugger Fonksiyonu");
                }
            }, 1000);
            handleVisibilityChange = () => {
                if (document.hidden) {
                    triggerAggressiveAction("Visibility: Sekme Değişimi");
                }
            };

            // Event Listener'ı ekle
            document.addEventListener("visibilitychange", handleVisibilityChange);

        }, 1000);

        return () => {
            // Gecikmeli başlatma zamanlayıcısını temizle
            clearTimeout(startProtectionTimer);

            // Eğer kontroller başlatıldıysa temizle
            if (handleVisibilityChange) {
                document.removeEventListener("visibilitychange", handleVisibilityChange);
            }
            if (checkDevTools) {
                clearInterval(checkDevTools);
            }
        };
    }, [location.pathname, triggerAggressiveAction]);

    // Klavye, Geliştirici Araçları ve Görünürlük Engelleri
    useEffect(() => {
        const path = location.pathname;

        // KRİTİK KONTROL: Korumayı DEVRE DIŞI BIRAKACAK ROTALAR
        const isSafeRoute = path.includes('/share/') || // Share kendi korumasını yönetir
            path.startsWith('/login') ||
            path.startsWith('/register') ||
            path.startsWith('/dashboard') ||
            path.startsWith('/memory') ||
            path.startsWith('/api') ||
            path === '/';

        if (isSafeRoute) {
            return; // Bu rotalarda listener kurulmaz
        };

        const handleKeyDown = (e) => {
            const protectedKeys = ['PrintScreen', 'Snapshot', 'F12'];

            // PrtScn tuşu ve F12 (DevTools) tuşu tespiti
            if (protectedKeys.includes(e.key) || e.keyCode === 44 || e.keyCode === 123) {
                e.preventDefault();
                e.stopPropagation();

                // Tuşa basıldığı an anında aksiyonu tetikle
                triggerAggressiveAction(e.key === 'F12' ? "Geliştirici Tuşu" : "Ekran Görüntüsü Tuşu");
                return false;
            }

            // Ctrl+Shift+I/J/C (DevTools kısayolları)
            if (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) {
                e.preventDefault();
                triggerAggressiveAction("Geliştirici Araçları Kısayolu");
                return false;
            }
        };

        // Kopyalama, Kesme ve Sağ Tık Engeli
        const handleContextMenu = (e) => {
            e.preventDefault();
            triggerAggressiveAction("Sağ Tık Menüsü");
            return false;
        };

        const handleCopyCutPaste = (e) => {
            e.preventDefault();
            triggerAggressiveAction("Kopyalama/Kesme/Yapıştırma");
            return false;
        };

        // Geliştirici Araçları (DevTools) Algılama (Konsol Hilesi)
        let devtoolsTest = /./;
        devtoolsTest.toString = function () {
            triggerAggressiveAction("Geliştirici Araçları (Konsol Kontrolü)");
        };

        const checkDevTools = setInterval(() => {
            // Yöntem 1: Boyut Kontrolü
            const widthThreshold = 160;
            if (window.outerWidth - window.innerWidth > widthThreshold ||
                window.outerHeight - window.innerHeight > widthThreshold) {
                triggerAggressiveAction("Geliştirici Araçları (Boyut Kontrolü)");
            }

            // Yöntem 2: Konsol Kontrolü
            console.log('%c', devtoolsTest);

        }, 1000);

        // Sekme Değişimi Tespiti
        const handleVisibilityChange = () => {
            if (document.hidden) {
                triggerAggressiveAction("Sekme Odağı/Görünürlük Kaybı");
            }
        };

        document.addEventListener('keydown', handleKeyDown, true);
        document.addEventListener('contextmenu', handleContextMenu, true);
        document.addEventListener('copy', handleCopyCutPaste, true);
        document.addEventListener('cut', handleCopyCutPaste, true);
        document.addEventListener("visibilitychange", handleVisibilityChange);

        return () => {
            document.removeEventListener('keydown', handleKeyDown, true);
            document.removeEventListener('contextmenu', handleContextMenu, true);
            document.removeEventListener('copy', handleCopyCutPaste, true);
            document.removeEventListener('cut', handleCopyCutPaste, true);
            document.removeEventListener("visibilitychange", handleVisibilityChange);
            clearInterval(checkDevTools);
        };
    }, [location.pathname, triggerAggressiveAction]);


    // Güvenlik alarmı aktifse tüm içeriği karartan katman
    if (isSecurityAlert) {
        return (
            <div
                style={{
                    position: 'fixed', // Ekranın neresinde olursa olsun sabit kalır
                    top: 0,
                    left: 0,
                    width: '100vw',    // Tüm genişlik
                    height: '100vh',   // Tüm yükseklik
                    backgroundColor: 'rgba(0, 0, 0, 1)', // Tam karartma
                    color: 'white',
                    zIndex: 99999, // Tüm elementlerin üstünde olmalı
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    fontSize: '24px',
                    textAlign: 'center'
                }}
            >
                <div style={{ fontSize: '72px', color: 'red', marginBottom: '20px' }}>🚫</div>
                <p>Güvenlik İhlali Tespit Edildi.</p>
                <p style={{ fontSize: '16px', color: '#ccc' }}>İçeriğe erişiminiz bu oturum için engellenmiştir.</p>
            </div>
        );
    }


    // Güvenlik alarmı yoksa hiçbir şey render etme
    return null;
};

export default GlobalProtection;
