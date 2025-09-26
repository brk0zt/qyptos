import React from 'react';

const Textarea = ({ placeholder, value, onChange, className = '', ...props }) => {
    return (
        <textarea
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            className={`text-input ${className}`}
            {...props}
        />
    );
};

// Named export kullanın
export { Textarea };