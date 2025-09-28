import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import LoginSignup from './components/LoginSignup';
import Dashboard from './components/Dashboard';
import './index.css';
import FileDetail from "./components/FileDetail";

<Routes>
    <Route path="/login" element={<LoginSignup />} />
    <Route path="/" element={<Dashboard />} />
    <Route path="/files/:fileId" element={<FileDetail />} />
</Routes>

function AppContent() {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState([]);

    // WebSocket bağlantısı - SADECE user varsa
    useEffect(() => {
        if (user) {
            console.log('WebSocket bağlantısı geçici olarak devre dışı');
            
            // const ws = new WebSocket('ws://localhost:8001/ws/notifications/');
            /*
            // ws.onopen = () => {
              //  console.log('WebSocket connected successfully');
            };

           // ws.onmessage = (event) => {
             //   try {
               //     const data = JSON.parse(event.data);
                 //   setNotifications((prev) => [data, ...prev]);
              //  } catch (error) {
                //    console.error('WebSocket message parsing error:', error);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
            };

            return () => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.close();
                }
            };
            */
        }
    }, [user]);
    
    const handleKayit = async (kayitData) => {
        try {
            console.log('Signup attempt:', kayitData);

            const response = await fetch('http://localhost:8001/api/auth/signup/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(kayitData)
            });

            console.log('Signup response status:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Signup response data:', data);

            return data;

        } catch (error) {
            console.error('Signup error:', error);
            throw error;
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
            <Route path="/login.html" element={<Navigate to="/login" replace />} />
        </Routes>
    );
}

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
