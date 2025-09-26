// App.jsx (düzeltilmiş)
import React from "react";
import { AuthProvider, useAuth } from '../AuthContext';
import LoginSignup from "./LoginSignup";
import Dashboard from "./Dashboard";
import ReactDOM from "react-dom/client";
import App from "../App";

function AppContent() {
    const { user, logout } = useAuth(); // AuthContext'ten kullanıcı ve çıkış fonksiyonunu al

    const apiBase = "http://localhost:8001/api";

    return (
        <div className="min-h-screen">
            {!user ? (
                // LoginSignup bileşenine apiBase prop'unu gönder
                <LoginSignup apiBase={apiBase} />
            ) : (
                // Dashboard bileşenine kullanıcı verisi ve logout fonksiyonunu gönder
                <Dashboard user={user} onLogout={logout} />
            )}
        </div>
    );
}

// Eğer kullanıcı login değilse LoginSignup açılır
if (!user) {
    return <LoginSignup />;
}

// Login olmuşsa Dashboard açılır
return <Dashboard />;


function App() {
    return (
        <AuthProvider>
            <AppContent />
        </AuthProvider>
    );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
    <React.StrictMode>
        <AuthProvider>
            <App />
        </AuthProvider>
    </React.StrictMode>
);
export default function App() {
    return (
        <AuthProvider>
            <AppContent />
        </AuthProvider>
    );
}


