import React from 'react';

// Named exports kullanın
export const Avatar = ({ src, alt, className = '' }) => {
    return (
        <img
            src={src}
            alt={alt}
            className={`w-8 h-8 rounded-full ${className}`}
        />
    );
};

export const AvatarFallback = ({ children, className = '' }) => {
    return (
        <div className={`w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center ${className}`}>
            <span className="text-sm font-medium text-gray-600">
                {children}
            </span>
        </div>
    );
};