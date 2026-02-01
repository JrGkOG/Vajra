import React from 'react';

export const Button = ({ children, onClick, type = 'button', className = '', ...props }) => {
    return (
        <button
            type={type}
            onClick={onClick}
            className={`brutal-btn ${className}`}
            {...props}
        >
            {children}
        </button>
    );
};
