import React, { useState } from 'react';

function LoginSignup({ onKayit }) {
    const [isLogin, setIsLogin] = useState(true);
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: ''
    });
    const [showPassword, setShowPassword] = useState(false);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    }; // BU FONKSİYON BURADA BİTMELİ - FAZLA KOD YOK!

    // Tarayıcı çerezlerinden CSRF jetonunu çeken yardımcı fonksiyon
    const getCSRFToken = () => {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        try {
            console.log('🔄 LOGIN İŞLEMİ BAŞLATILIYOR...');
            console.log('📧 Email:', formData.email);
            console.log('🔐 Password:', '*'.repeat(formData.password.length));

            const endpoint = isLogin ? 'login' : 'signup';
            const url = `http://localhost:8001/api/auth/${endpoint}/`;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(isLogin ? {
                    email: formData.email,
                    password: formData.password
                } : formData)
            });

            console.log('📡 RESPONSE STATUS:', response.status);
            console.log('📡 RESPONSE HEADERS:', response.headers);

            const contentType = response.headers.get('content-type');
            console.log('📋 CONTENT TYPE:', contentType);

            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                console.log('📦 TAM RESPONSE DATA:', data);

                if (response.ok) {
                    if (isLogin) {
                        // ⚠️ KRİTİK: Token'ları kontrol et ve kaydet
                        console.log('🔑 ACCESS TOKEN:', data.access);
                        console.log('🔄 REFRESH TOKEN:', data.refresh);
                        console.log('👤 USER DATA:', data.user);

                        if (!data.access) {
                            console.error('❌ ACCESS TOKEN ALINAMADI!');
                            alert('Backend access token döndürmedi!');
                            return;
                        }

                        if (!data.refresh) {
                            console.error('❌ REFRESH TOKEN ALINAMADI!');
                            alert('Backend refresh token döndürmedi!');
                            return;
                        }

                        // Token'ları kaydet
                        localStorage.setItem('token', data.access); // 'access_token' yerine 'token'
                        localStorage.setItem('refresh', data.refresh); // 'refresh_token' yerine 'refresh'
                        localStorage.setItem('user', JSON.stringify(data.user));

                        // Kaydedildiğini kontrol et
                        console.log('✅ LOCALSTORAGE KONTROL:');
                        console.log('   - atoken:', localStorage.getItem('token') ? '✅ VAR' : '❌ YOK');
                        console.log('   - refresh:', localStorage.getItem('refresh') ? '✅ VAR' : '❌ YOK');
                        console.log('   - user:', localStorage.getItem('user') ? '✅ VAR' : '❌ YOK');

                        console.log('🎯 DASHBOARDA YÖNLENDİRİLİYOR...');
                        window.location.href = '/dashboard';

                    } else {
                        alert('Kayıt başarılı! Giriş yapabilirsiniz.');
                        setIsLogin(true);
                        setFormData({ username: '', email: '', password: '' });
                    }
                } else {
                    console.error('❌ RESPONSE NOT OK:', data);
                    alert(data.detail || data.message || `İşlem başarısız! Status: ${response.status}`);
                }
            } else {
                const text = await response.text();
                console.error('❌ BEKLENMEYEN FORMAT:', text);
                alert(`Sunucu hatası: ${response.status}. Lütfen konsolu kontrol edin.`);
            }

        } catch (error) {
            console.error('❌ AUTH ERROR:', error);
            alert(`İşlem sırasında hata oluştu: ${error.message}`);
        }
    };
    return (
        <div className="login-signup-container">
            {/* ... Formun geri kalanı ... */}
            {isLogin ? (
                // LOGIN FORM
                <div className="form-section">
                    <h1>Giriş Yap</h1>
                    <form onSubmit={handleSubmit}>
                        {/* ... Giriş alanları ... */}
                        <div className="input-group">
                            <label>E-posta/Telefon Numarası</label>
                            <i className="fas fa-envelope input-icon"></i>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                placeholder="E-posta adresinizi ya da telefon numaranızı girin"
                                required
                            />
                        </div>

                        <div className="input-group">
                            <label>Şifre</label>
                            <i className="fas fa-lock input-icon"></i>
                            <input
                                type={showPassword ? "text" : "password"}
                                name="password"
                                value={formData.password}
                                onChange={handleInputChange}
                                placeholder="Şifrenizi girin"
                                required
                            />
                            <i
                                className={`fas fa-eye${showPassword ? '-slash' : ''} password-toggle`}
                                onClick={() => setShowPassword(!showPassword)}
                            ></i>
                        </div>

                        <button type="submit" className="submit-btn">
                            Giriş Yap
                        </button>
                    </form>

                    <p className="toggle-text">
                        Hesabınız yok mu? {' '}
                        <button
                            type="button"
                            onClick={() => setIsLogin(false)}
                            className="toggle-btn"
                        >
                            Kayıt Ol
                        </button>
                    </p>
                </div>
            ) : (
                // SIGNUP FORM
                <div className="form-section">
                    <h1>Kayıt Ol</h1>
                    <form onSubmit={handleSubmit}>
                        <div className="input-group">
                            <label>Kullanıcı Adı</label>
                            <i className="fas fa-user input-icon"></i>
                            <input
                                type="text"
                                name="username"
                                value={formData.username}
                                onChange={handleInputChange}
                                placeholder="Kullanıcı adınızı girin"
                                required
                            />
                        </div>

                        <div className="input-group">
                            <label>E-posta/Telefon Numarası</label>
                            <i className="fas fa-envelope input-icon"></i>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                placeholder="E-posta adresinizi ya da telefon numaranızı girin"
                                required
                            />
                        </div>

                        <div className="input-group">
                            <label>Şifre</label>
                            <i className="fas fa-lock input-icon"></i>
                            <input
                                type={showPassword ? "text" : "password"}
                                name="password"
                                value={formData.password}
                                onChange={handleInputChange}
                                placeholder="Şifrenizi girin"
                                required
                            />
                            <i
                                className={`fas fa-eye${showPassword ? '-slash' : ''} password-toggle`}
                                onClick={() => setShowPassword(!showPassword)}
                            ></i>
                        </div>

                        <button type="submit" className="submit-btn">
                            Kayıt Ol
                        </button>
                    </form>

                    <p className="toggle-text">
                        Zaten hesabınız var mı? {' '}
                        <button
                            type="button"
                            onClick={() => setIsLogin(true)}
                            className="toggle-btn"
                        >
                            Giriş Yap
                        </button>
                    </p>
                </div>
            )}
        </div>
    );
}

export default LoginSignup;