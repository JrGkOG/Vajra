import React from 'react';
import { ViewMyKeys } from '../keys/ViewMyKeys';

export const KeysPage = ({ token }) => {
    return (
        <div className="min-h-screen bg-brutal-bg p-8">
            <ViewMyKeys token={token} />
        </div>
    );
};
