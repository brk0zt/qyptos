import React from 'react';


export const Button = ({ children, onClick, variant = 'default', className = '', ...props }) => {
    const baseStyle = "px-4 py-2 rounded font-medium focus:outline-none focus:ring-2 transition-colors";
    const variants = {
        default: "bg-blue-500 text-white hover:bg-blue-600",
        outline: "border border-gray-300 text-gray-700 hover:bg-gray-50",
        ghost: "text-gray-700 hover:bg-gray-100",
        destructive: "bg-red-500 text-white hover:bg-red-600"
    };

    return (
        <button
            className={`${baseStyle} ${variants[variant]} ${className}`}
            onClick={onClick}
            {...props}
        >
            {children}
        </button>
    );
};