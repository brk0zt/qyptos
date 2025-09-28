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

    const login = (userData, accessToken, newRefreshToken) => {
        setUser(userData);
        setToken(accessToken);
        setRefreshToken(newRefreshToken);
        localStorage.setItem("user", JSON.stringify(userData));
        localStorage.setItem("token", accessToken);
        localStorage.setItem("refresh", newRefreshToken);
    };

    const logout = async () => {
        try {
            if (refreshToken) {
                await fetch("http://127.0.0.1:8001/auth/logout/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ refresh: refreshToken }),
                });
            }
        } catch (err) {
            console.error("Logout istegi basarisiz:", err);
        }

        setUser(null);
        setToken(null);
        setRefreshToken(null);
        localStorage.removeItem("user");
        localStorage.removeItem("token");
        localStorage.removeItem("refresh");
    };

    const refreshAccessToken = async () => {
        if (!refreshToken) {
            logout();
            return;
        }

        try {
            const res = await fetch("http://127.0.0.1:8001/api/token/refresh/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh: refreshToken }),
            });

            if (res.ok) {
                const data = await res.json();
                setToken(data.access);
                localStorage.setItem("token", data.access);
                return data.access;
            } else {
                logout();
            }
        } catch (err) {
            console.error("Token yenileme hatası:", err);
            logout();
        }
    };

    // Token yenileme interval'i
    useEffect(() => {
        if (refreshToken) {
            const interval = setInterval(refreshAccessToken, 4 * 60 * 1000); // 4 dakikada bir
            return () => clearInterval(interval);
        }
    }, [refreshToken]);

    // Başlangıçta token kontrolü (isteğe bağlı)
    useEffect(() => {
        if (token && refreshToken) {
            // Token hala geçerli mi kontrol et
            const checkTokenValidity = async () => {
                try {
                    const res = await fetch("http://127.0.0.1:8001/api/verify-token/", {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (!res.ok) {
                        await refreshAccessToken();
                    }
                } catch (err) {
                    console.error("Token geçerlilik kontrolü hatası:", err);
                }
            };

            checkTokenValidity();
        }
    }, []);

    // Context değerini açıkça tanımlayın
    const value = {
        user,
        token,
        refreshToken,
        login,
        logout,
        refreshAccessToken,
        redirectTo,
        setRedirectTo
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