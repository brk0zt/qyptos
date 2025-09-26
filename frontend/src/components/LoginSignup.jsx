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

    const handleSubmit = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (isLogin) {
            try {
                console.log('Login attempt:', formData);

                const response = await fetch('http://localhost:8001/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken(), 
                    },
                    body: JSON.stringify({
                        email: formData.email,
                        password: formData.password
                    })
                });

                console.log('Request method: POST');
                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Response data:', data);

                if (response.ok && data.success) {
                    localStorage.setItem('token', data.token);
                    window.location.href = '/dashboard';
                } else {
                    alert(data.message || `Giriş başarısız! Status: ${response.status}`);
                }
            } catch (error) {
                console.error('Login error:', error);
                alert(`Giriş sırasında hata oluştu: ${error.message}`);
            }
        } else {
            // Signup logic (mevcut kodun)
            const result = await onKayit(formData);
            if (result && result.success) {
                setIsLogin(true);
                setFormData({ username: '', email: '', password: '' });
            }
        }
    };

    const getCSRFToken = () => {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    };

    return (
        <div className="login-signup-container">
            {isLogin ? (
                // LOGIN FORM
                <div className="form-section">
                    <h1>Giriş Yap</h1>
                    <form onSubmit={handleSubmit}>
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