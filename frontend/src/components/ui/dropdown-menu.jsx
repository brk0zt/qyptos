import React, { useState } from 'react';

// Named exports kullanın
export const DropdownMenu = ({ children }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="relative">
            {React.Children.map(children, child =>
                React.cloneElement(child, { isOpen, setIsOpen })
            )}
        </div>
    );
};

export const DropdownMenuTrigger = ({ children, isOpen, setIsOpen }) => {
    return (
        <div onClick={() => setIsOpen(!isOpen)} className="cursor-pointer">
            {children}
        </div>
    );
};

export const DropdownMenuContent = ({ children, isOpen }) => {
    if (!isOpen) return null;

    return (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border">
            {children}
        </div>
    );
};

export const DropdownMenuLabel = ({ children }) => {
    return (
        <div className="px-4 py-2 text-sm font-semibold text-gray-900">
            {children}
        </div>
    );
};

export const DropdownMenuSeparator = () => {
    return <div className="border-t my-1" />;
};

export const DropdownMenuItem = ({ children, onClick, className = "" }) => {
    return (
        <div
            className={`px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer ${className}`}
            onClick={onClick}
        >
            {children}
        </div>
    );
};