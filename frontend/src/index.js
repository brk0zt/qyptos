import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

const rootElement = document.getElementById('root');

if (rootElement) {
    const root = ReactDOM.createRoot(rootElement);
    root.render(
        <React.StrictMode>
            <BrowserRouter>
                <App />
            </BrowserRouter>
        </React.StrictMode>
    );
} else {
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
}