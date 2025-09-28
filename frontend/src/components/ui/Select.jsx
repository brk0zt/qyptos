import React, { createContext, useContext, useState, useRef, useEffect } from 'react';

const SelectContext = createContext();

const Select = ({ children, value, onValueChange }) => {
    const [isOpen, setIsOpen] = useState(false);
    const selectRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (selectRef.current && !selectRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <SelectContext.Provider value={{ isOpen, setIsOpen, value, onValueChange }}>
            <div className="relative" ref={selectRef}>
                {children}
            </div>
        </SelectContext.Provider>
    );
};

const SelectTrigger = React.forwardRef(({ children, className = '', ...props }, ref) => {
    const { isOpen, setIsOpen } = useContext(SelectContext);

    return (
        <button
            ref={ref}
            className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
            onClick={() => setIsOpen(!isOpen)}
            {...props}
        >
            {children}
        </button>
    );
});

const SelectValue = ({ placeholder }) => {
    const { value } = useContext(SelectContext);
    return <span className="block truncate">{value || placeholder}</span>;
};

const SelectContent = ({ children, className = '' }) => {
    const { isOpen } = useContext(SelectContext);

    if (!isOpen) return null;

    return (
        <div className={`absolute z-50 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg ${className}`}>
            <div className="p-1">
                {children}
            </div>
        </div>
    );
};

const SelectItem = React.forwardRef(({ children, value, className = '', ...props }, ref) => {
    const { onValueChange, setIsOpen } = useContext(SelectContext);

    const handleSelect = () => {
        onValueChange(value);
        setIsOpen(false);
    };

    return (
        <button
            ref={ref}
            className={`relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-2 pr-8 text-sm outline-none hover:bg-gray-100 focus:bg-gray-100 ${className}`}
            onClick={handleSelect}
            {...props}
        >
            {children}
        </button>
    );
});

SelectTrigger.displayName = 'SelectTrigger';
SelectValue.displayName = 'SelectValue';
SelectContent.displayName = 'SelectContent';
SelectItem.displayName = 'SelectItem';

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };