// frontend/src/contexts/MemoryContext.js
import React, { createContext, useState, useContext, useCallback } from 'react';
import axios from 'axios';

const MemoryContext = createContext();

export const useMemory = () => {
    return useContext(MemoryContext);
};

export const MemoryProvider = ({ children }) => {
    const [suggestions, setSuggestions] = useState([]);
    const [isLearning, setIsLearning] = useState(true);
    const [memoryStats, setMemoryStats] = useState(null);

    // Memory istatistiklerini getir
    const fetchMemoryStats = useCallback(async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get('http://localhost:8001/api/memory/stats/', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });
            setMemoryStats(response.data);
            return response.data;
        } catch (error) {
            console.error('Fetch memory stats error:', error);
            // Fallback stats
            const fallbackStats = {
                used_memory: 2.5,
                total_memory: 10,
                total_items: 25,
                total_activities: 150,
                file_type_count: 8
            };
            setMemoryStats(fallbackStats);
            return fallbackStats;
        }
    }, []);

    // Kullanýcý aktivitesini takip et
    const trackActivity = useCallback(async (activityType, data) => {
        try {
            const token = localStorage.getItem('token');
            await axios.post('http://localhost:8001/api/memory/activity/track/', {
                activity_type: activityType,
                data: data,
                timestamp: new Date().toISOString()
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });
        } catch (error) {
            console.error('Activity tracking error:', error);
        }
    }, []);

    // Önerileri getir
    const fetchSuggestions = useCallback(async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get('http://localhost:8001/api/memory/suggestions/', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });
            setSuggestions(response.data);
            return response.data;
        } catch (error) {
            console.error('Fetch suggestions error:', error);
        }
    }, []);

    const value = {
        suggestions,
        isLearning,
        memoryStats,
        trackActivity,
        fetchSuggestions,
        fetchMemoryStats
    };

    return (
        <MemoryContext.Provider value={value}>
            {children}
        </MemoryContext.Provider>
    );
};