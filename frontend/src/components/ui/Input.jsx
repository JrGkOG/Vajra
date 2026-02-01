import React from 'react';

export const Input = ({ type = 'text', placeholder, value, onChange, className = '', ...props }) => {
    return (
        <input
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            className={`brutal-input ${className}`}
            {...props}
        />
    );
};
