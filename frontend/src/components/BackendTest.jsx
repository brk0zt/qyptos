import React, { useState } from 'react';
import { authAPI, groupAPI } from '../utils/api';

const BackendTest = () => {
    const [status, setStatus] = useState('Test ediliyor...');
    const [results, setResults] = useState({});

    const testBackend = async () => {
        setStatus('Backend test ediliyor...');

        const testResults = {};

        try {
            // Test 1: Auth endpoint
            const authTest = await authAPI.checkAuth();
            testResults.auth = '✅ Çalışıyor';
        } catch (error) {
            testResults.auth = `❌ Hata: ${error.response?.status || error.message}`;
        }

        try {
            // Test 2: Groups endpoint
            const groupsTest = await groupAPI.getGroups();
            testResults.groups = '✅ Çalışıyor';
        } catch (error) {
            testResults.groups = `❌ Hata: ${error.response?.status || error.message}`;
        }

        setResults(testResults);
        setStatus('Test tamamlandı');
    };

    return (
        <div className="p-4 bg-gray-100 rounded-lg">
            <h3 className="text-lg font-bold mb-2">Backend Bağlantı Testi</h3>
            <button
                onClick={testBackend}
                className="px-4 py-2 bg-blue-500 text-white rounded mb-4"
            >
                Backend'i Test Et
            </button>

            <div className="space-y-2">
                <div><strong>Auth Endpoint:</strong> {results.auth || 'Test edilmedi'}</div>
                <div><strong>Groups Endpoint:</strong> {results.groups || 'Test edilmedi'}</div>
            </div>

            <div className="mt-4 text-sm text-gray-600">
                <p><strong>Backend URL:</strong> http://localhost:8001/api/</p>
                <p><strong>Frontend URL:</strong> http://localhost:3000/</p>
            </div>
        </div>
    );
};

export default BackendTest;