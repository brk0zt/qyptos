import { useAuth } from "../AuthContext";

export function useApi() {
    const { token, refreshToken, login, logout, user } = useAuth();

    const apiFetch = async (url, options = {}) => {
        let headers = {
            ...(options.headers || {}),
            "Content-Type": "application/json",
        };

        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        try {
            let response = await fetch(url, { ...options, headers });

            // Eğer token expired / geçersiz → refresh token dene
            if (response.status === 401 && refreshToken) {
                console.log("⏳ Access token expired, refreshing...");

                const refreshRes = await fetch("http://127.0.0.1:8001/api/token/refresh/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ refresh: refreshToken }),
                });

                if (refreshRes.ok) {
                    const data = await refreshRes.json();
                    // Yeni access token kaydet
                    login(user, data.access, refreshToken);

                    // Tekrar dene (bu sefer yeni token ile)
                    headers["Authorization"] = `Bearer ${data.access}`;
                    response = await fetch(url, { ...options, headers });
                } else {
                    console.log("❌ Refresh token gecersiz → logout");
                    logout();
                }
            }

            return response;
        } catch (err) {
            console.error("API istegi basarisiz:", err);
            throw err;
        }
    };

    return { apiFetch };
}


