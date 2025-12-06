// App.js - DÜZELTÝLMÝÞ VERSÝYON
import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import { MemoryProvider } from './components/MemoryContext';
import LoginSignup from './components/LoginSignup';
import Dashboard from './components/Dashboard';
import GlobalProtection from './components/GlobalProtection';
import SecureFileViewer from './components/SecureFileViewer';
import './index.css';

function AppContent() {
    const { user, loading } = useAuth();
    const apiBase = "http://localhost:8001/api";

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100vh'
            }}>
                <p>Yükleniyor...</p>
            </div>
        );
    }

    return (
        <Routes>
            {/* KRÝTÝK DÜZELTME: /share/:token rotasýný düzgün þekilde tanýmla */}
            <Route
                path="/share/:token"
                element={<SecureFileViewer />}
            />

            {/* Dashboard ve login rotalarý */}
            <Route
                path="/login"
                element={!user ? <LoginSignup apiBase={apiBase} /> : <Navigate to="/dashboard" replace />}
            />
            <Route
                path="/dashboard"
                element={user ? <Dashboard /> : <Navigate to="/login" replace />}
            />

            {/* Kök route yönlendirmesi */}
            <Route
                path="/"
                element={<Navigate to={user ? "/dashboard" : "/login"} replace />}
            />

            {/* Eþleþmeyen diðer tüm rotalar */}
            <Route
                path="*"
                element={<Navigate to={user ? "/dashboard" : "/login"} replace />}
            />
        </Routes>
    );
}

export default function App() {
    return (
        <AuthProvider>
            <GlobalProtection />
            <MemoryProvider>
                <AppContent />
            </MemoryProvider>
        </AuthProvider>
    );
}