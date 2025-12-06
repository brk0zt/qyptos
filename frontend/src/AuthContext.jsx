import React, { createContext, useState, useContext, useEffect } from "react";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    // Kullanıcı bilgisini localStorage'dan yükle
    const [user, setUser] = useState(() => {
        const savedUser = localStorage.getItem('user');
        return savedUser ? JSON.parse(savedUser) : null;
    });
    const [redirectTo, setRedirectTo] = useState(null);
    const [token, setToken] = useState(() => {
        return localStorage.getItem("token") || null;
    });
    const [refreshToken, setRefreshToken] = useState(() => {
        return localStorage.getItem("refresh") || null;
    });
    const [loading, setLoading] = useState(true); // loading state'ini buraya taşı

    // Loading state'ini yönet
    useEffect(() => {
        // İlk yüklemede loading'i false yap
        setLoading(false);
    }, []);

    const login = (userData, accessToken, newRefreshToken) => {
        console.log('🔐 AuthContext login çağrıldı');
        setUser(userData);
        setToken(accessToken);
        setRefreshToken(newRefreshToken);
        localStorage.setItem("user", JSON.stringify(userData));
        localStorage.setItem("token", accessToken);
        localStorage.setItem("refresh", newRefreshToken);
        console.log('✅ AuthContext - Kullanıcı bilgileri kaydedildi');
    };

    const logout = () => {
        console.log('🚪 AuthContext logout çağrıldı');
        setUser(null);
        setToken(null);
        setRefreshToken(null);
        localStorage.removeItem("user");
        localStorage.removeItem("token");
        localStorage.removeItem("refresh");
        console.log('✅ AuthContext - Tüm veriler temizlendi');

        // Login sayfasına yönlendir
        window.location.href = '/login';
    };

    // Basit token kontrolü
    const checkTokenValidity = async () => {
        const currentToken = localStorage.getItem('token');
        if (!currentToken) {
            console.log('❌ Token bulunamadı');
            logout();
            return false;
        }
        return true;
    };

    // Context değerini açıkça tanımlayın
    const value = {
        user,
        token,
        refreshToken,
        login,
        logout,
        checkTokenValidity,
        redirectTo,
        setRedirectTo,
        loading
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};