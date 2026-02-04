import React from 'react';
import { KeyManagement } from '../keys/KeyManagement';

export const GenerateKeysPage = ({ token }) => {
    return (
        <div className="min-h-screen bg-brutal-bg p-8">
            <KeyManagement token={token} />
        </div>
    );
};
