import React from 'react';

const Input = ({ type = 'text', placeholder, value, onChange, className = '', ...props }) => {
    return (
        <input
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            className={`text-input ${className}`}
            {...props}
        />
    );
};

// Named export kullanın
export { Input };