class CameraSecurity {
    constructor() {
        this.isMonitoring = false;
        this.securityBreach = false;
        this.videoElement = null;
        this.canvasElement = null;
        this.mediaStream = null;
    }

    async startMonitoring() {
        try {
            // Kameraya erişim izni iste
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: 640, 
                    height: 480,
                    facingMode: 'user'
                } 
            });
            
            this.videoElement = document.createElement('video');
            this.videoElement.srcObject = this.mediaStream;
            this.videoElement.play();
            
            this.canvasElement = document.createElement('canvas');
            this.canvasElement.width = 640;
            this.canvasElement.height = 480;
            
            this.isMonitoring = true;
            this.monitorFrame();
            
            console.log('Kamera güvenlik izlemesi başlatıldı');
            
        } catch (error) {
            console.error('Kamera erişim hatası:', error);
            // Kameraya erişilemezse yine de içeriği göster
            this.showContent();
        }
    }

    async monitorFrame() {
        if (!this.isMonitoring) return;

        const context = this.canvasElement.getContext('2d');
        context.drawImage(this.videoElement, 0, 0, 640, 480);
        
        // Frame'i backend'e gönder ve analiz et
        this.canvasElement.toBlob(async (blob) => {
            try {
                const formData = new FormData();
                formData.append('frame', blob);
                
                const response = await fetch('/api/security/analyze-frame/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                const result = await response.json();
                
                if (result.security_breach) {
                    this.handleSecurityBreach(result.reason);
                } else {
                    this.showContent();
                }
                
                // Sonraki frame için devam et
                if (this.isMonitoring) {
                    setTimeout(() => this.monitorFrame(), 100); // 10 FPS
                }
                
            } catch (error) {
                console.error('Frame analiz hatası:', error);
                this.showContent();
            }
        }, 'image/jpeg', 0.8);
    }

    handleSecurityBreach(reason) {
        this.securityBreach = true;
        this.stopMonitoring();
        
        // Ekranı karart
        document.body.style.backgroundColor = 'black';
        
        // Tüm medya elementlerini gizle
        const mediaElements = document.querySelectorAll('img, video, iframe');
        mediaElements.forEach(el => {
            el.style.visibility = 'hidden';
        });
        
        // Uyarı mesajı göster
        this.showSecurityWarning(reason);
        
        // Backend'e güvenlik ihlalini bildir
        this.reportSecurityBreach(reason);
    }

    showSecurityWarning(reason) {
        const warningDiv = document.createElement('div');
        warningDiv.innerHTML = `
            <div style="
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #ff4444;
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                z-index: 9999;
            ">
                <h2>🚨 GÜVENLİK UYARISI</h2>
                <p>Güvenlik nedeniyle içerik engellendi</p>
                <small>Sebep: ${reason}</small>
            </div>
        `;
        document.body.appendChild(warningDiv);
    }

    showContent() {
        // İçeriği normale döndür
        document.body.style.backgroundColor = '';
        const mediaElements = document.querySelectorAll('img, video, iframe');
        mediaElements.forEach(el => {
            el.style.visibility = 'visible';
        });
    }

    stopMonitoring() {
        this.isMonitoring = false;
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
    }

    async reportSecurityBreach(reason) {
        try {
            await fetch('/api/security/report-breach/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    reason: reason,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.error('Güvenlik ihlali raporlama hatası:', error);
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Global instance
window.cameraSecurity = new CameraSecurity();

// Sayfa yüklendiğinde kamera güvenliğini başlat
document.addEventListener('DOMContentLoaded', function() {
    // Sadece tek kullanımlık medya sayfalarında çalışsın
    if (window.location.pathname.includes('/one-time-view/') || 
        window.location.pathname.includes('/share/') ||
        window.location.pathname.includes('/preview/')) {
        
        setTimeout(() => {
            window.cameraSecurity.startMonitoring();
        }, 1000);
    }
});