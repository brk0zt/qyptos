import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AuthProvider } from './AuthContext';
import './index.css';

const rootElement = document.getElementById('root');

if (rootElement) {
    const root = ReactDOM.createRoot(rootElement);
    root.render(
        <React.StrictMode>
            <App />
        </React.StrictMode>
    );
} 
else if (!rootElement) {
    // DOM'da "root" ID'li element yoksa hata mesajý göster
    const errorMessage = document.createElement('div');
    errorMessage.style.cssText = `
        padding: 20px;
        margin: 20px;
        border: 2px solid red;
        border-radius: 5px;
        background-color: #ffeeee;
        color: #cc0000;
        font-family: Arial, sans-serif;
    `;
    errorMessage.innerHTML = `
        <h2>React Uygulama Hatasý</h2>
        <p><strong>Hata:</strong> "root" ID'li element bulunamadý.</p>
        <p><strong>Çözüm:</strong> public/index.html dosyanýzda aþaðýdaki kodu ekleyin:</p>
        <pre>&lt;div id="root"&gt;&lt;/div&gt;</pre>
        <p>Veya mevcut elementin ID'sini kontrol edin.</p>
    `;

    document.body.appendChild(errorMessage);

} else {
    // "root" elementi bulunduysa uygulamayý baþlat
    const root = ReactDOM.createRoot(rootElement);

    root.render(
        <React.StrictMode>
            <AuthProvider>
                <App />
            </AuthProvider>
        </React.StrictMode>
    );
}
