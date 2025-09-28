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
    };

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
            const endpoint = isLogin ? 'login' : 'signup';
            const url = `http://localhost:8001/api/auth/${endpoint}/`;

            console.log(`${isLogin ? 'Login' : 'Signup'} attempt:`, formData);

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',  // Cookie'ler için önemli
                body: JSON.stringify(isLogin ? {
                    email: formData.email,  // LoginView artık email bekliyor
                    password: formData.password
                } : formData)
            });

            console.log('Response status:', response.status);

            // Önce response'ın JSON olup olmadığını kontrol et
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                console.log('Response data:', data);

                if (response.ok && data.success) {
                    if (isLogin) {
                        // JWT token'ı localStorage'a kaydet
                        localStorage.setItem('access_token', data.access);
                        localStorage.setItem('refresh_token', data.refresh);
                        localStorage.setItem('user', JSON.stringify(data.user));

                        window.location.href = '/dashboard';
                    } else {
                        alert('Kayıt başarılı! Giriş yapabilirsiniz.');
                        setIsLogin(true);
                        setFormData({ username: '', email: '', password: '' });
                    }
                } else {
                    alert(data.message || `İşlem başarısız! Status: ${response.status}`);
                }
            } else {
                const text = await response.text();
                console.error('Beklenmeyen yanıt formatı:', text);
                alert(`Sunucu hatası: ${response.status}. Lütfen konsolu kontrol edin.`);
            }

        } catch (error) {
            console.error('Auth error:', error);
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
                            <label>E-posta</label>
                            <i className="fas fa-envelope input-icon"></i>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                placeholder="E-posta adresinizi girin"
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
                            <label>E-posta</label>
                            <i className="fas fa-envelope input-icon"></i>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                placeholder="E-posta adresinizi girin"
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