// Card.jsx - Doğru versiyon
import React from 'react';

// Card bileşeni
const Card = ({ children, className = '' }) => {
    return (
        <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
            {children}
        </div>
    );
};

// CardHeader bileşeni
const CardHeader = ({ children, className = '' }) => {
    return (
        <div className={`border-b pb-2 mb-4 ${className}`}>
            {children}
        </div>
    );
};

// CardContent bileşeni
const CardContent = ({ children, className = '' }) => {
    return (
        <div className={className}>
            {children}
        </div>
    );
};

// Sadece bir kez export yapın
export { Card, CardHeader, CardContent };