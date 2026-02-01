import React from 'react';

export const Card = ({ children, title, className = '' }) => {
    return (
        <div className={`brutal-card ${className}`}>
            {title && <h2 className="text-2xl mb-6 border-b-4 border-black pb-2">{title}</h2>}
            {children}
        </div>
    );
};
