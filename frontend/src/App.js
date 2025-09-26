import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import LoginSignup from './components/LoginSignup';
import Dashboard from './components/Dashboard';
import './index.css';

// Auth durumuna göre yönlendirme yapan bileşen
function AppContent() {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState([]);

    // WebSocket bağlantısı - useEffect içinde
    useEffect(() => {
        // WebSocket bağlantısını sadece kullanıcı giriş yapmışsa kur
        if (user) {
            const ws = new WebSocket('ws://localhost:3000');

            ws.onopen = () => {
                console.log('WebSocket connected successfully');
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setNotifications((prev) => [data, ...prev]);
                } catch (error) {
                    console.error('WebSocket message parsing error:', error);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
            };

            // Cleanup function
            return () => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.close();
                }
            };
        }
    }, [user]); // user değiştiğinde yeniden bağlan

    const handleKayit = async (userData) => {
        try {
            const response = await fetch('http://localhost:8001/files/kayit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            const result = await response.json();
            console.log('Kayıt başarılı:', result);
            return result;
        } catch (error) {
            console.error('Kayıt hatası:', error);
            return null;
        }
    };

    return (
        <Routes>
            <Route
                path="/login"
                element={!user ? <LoginSignup onKayit={handleKayit} /> : <Navigate to="/dashboard" replace />}
            />
            <Route
                path="/dashboard"
                element={user ? <Dashboard notifications={notifications} /> : <Navigate to="/login" replace />}
            />
            <Route
                path="/"
                element={<Navigate to={user ? "/dashboard" : "/login"} replace />}
            />
            {/* Redirect login.html to login */}
            <Route path="/login.html" element={<Navigate to="/login" replace />} />
        </Routes>
    );
}

// Ana App bileşeni
function App() {
    return (
        <Router>
            <AuthProvider>
                <AppContent />
            </AuthProvider>
        </Router>
    );
}

export default App;
