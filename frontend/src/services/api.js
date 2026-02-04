/**
 * API Service Layer for communicating with the FastAPI backend.
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Step 1: Send email and password, receive MFA code via email
 * @param {string} email 
 * @param {string} password 
 * @returns {Promise<{success: boolean, message: string}>}
 */
export async function loginPassword(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login/password`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Password verification failed');
    }

    return await response.json();
}

/**
 * Step 2: Verify MFA code and get JWT token
 * @param {string} email 
 * @param {string} mfaCode - 6-digit code from email
 * @returns {Promise<{success: boolean, access_token: string, user: object}>}
 */
export async function loginMFA(email, mfaCode) {
    const response = await fetch(`${API_BASE_URL}/auth/login/mfa`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, mfa_code: mfaCode })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'MFA verification failed');
    }

    return await response.json();
}

/**
 * OLD Login (DEPRECATED - kept for backward compatibility)
 */
export async function login(username, password) {
    const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
    }

    return await response.json();
}

/**
 * Upload a file with encryption
 * @param {File} file 
 * @param {string} classification - 'top_secret', 'mission_logs', or 'public'
 * @param {string} token - JWT token
 * @returns {Promise<object>}
 */
export async function uploadFile(file, classification, token, vaultPassword = null) {
    const formData = new FormData();
    formData.append('file', file);

    // Build URL with classification and optional vault_password for signing
    let url = `${API_BASE_URL}/upload?classification=${classification}`;
    if (vaultPassword) {
        url += `&vault_password=${encodeURIComponent(vaultPassword)}`;
    }

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
    }

    return await response.json();
}

/**
 * Get list of all files
 * @param {string} token - JWT token
 * @returns {Promise<{success: boolean, files: array}>}
 */
export async function getFiles(token) {
    const response = await fetch(`${API_BASE_URL}/files`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch files');
    }

    return await response.json();
}

/**
 * Download a file
 * @param {string} fileId 
 * @param {string} encryptionKey - Hex-encoded key
 * @param {string} token - JWT token
 * @returns {Promise<Blob>}
 */
export async function downloadFile(fileId, encryptionKey, token) {
    const response = await fetch(`${API_BASE_URL}/download/${fileId}?key=${encryptionKey}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Download failed');
    }

    return await response.blob();
}

// ===== VAULT API FUNCTIONS =====

/**
 * Send MFA code for vault operations
 * @param {string} token - JWT token
 * @param {string} purpose - 'vault_store' or 'vault_retrieve'
 */
export async function sendVaultMFA(token, purpose = 'vault_retrieve') {
    const response = await fetch(`${API_BASE_URL}/vault/mfa/send?purpose=${purpose}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send MFA code');
    }

    return await response.json();
}

/**
 * Store encryption key in vault
 * @param {string} hexKey - Encryption key in hex format
 * @param {string} password - Vault password
 * @param {string} mfaCode - 6-digit MFA code
 * @param {string} fileId - Optional file ID
 * @param {string} keyLabel - Optional label for the key
 * @param {string} token - JWT token
 */
export async function storeKeyInVault(hexKey, password, mfaCode, fileId, keyLabel, token) {
    const response = await fetch(`${API_BASE_URL}/vault/store`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            hex_key: hexKey,
            password,
            mfa_code: mfaCode,
            file_id: fileId,
            key_label: keyLabel
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to store key in vault');
    }

    return await response.json();
}

/**
 * Retrieve encryption key from vault
 * @param {string} vaultId - Vault entry ID
 * @param {string} password - Vault password
 * @param {string} mfaCode - 6-digit MFA code
 * @param {string} token - JWT token
 */
export async function retrieveKeyFromVault(vaultId, password, mfaCode, token) {
    const response = await fetch(`${API_BASE_URL}/vault/retrieve`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            vault_id: vaultId,
            password,
            mfa_code: mfaCode
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to retrieve key from vault');
    }

    return await response.json();
}

/**
 * List all vault keys for user
 * @param {string} token - JWT token
 */
export async function listVaultKeys(token) {
    const response = await fetch(`${API_BASE_URL}/vault/list`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to list vault keys');
    }

    return await response.json();
}

/**
 * Delete a vault key
 * @param {string} vaultId - Vault entry ID
 * @param {string} token - JWT token
 */
export async function deleteVaultKey(vaultId, token) {
    const response = await fetch(`${API_BASE_URL}/vault/${vaultId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete vault key');
    }

    return await response.json();
}

// ===== SYSTEM STATUS API FUNCTIONS =====

/**
 * Get system status and metrics
 * @param {string} token - JWT token
 * NOTE: This is currently mocked data. Replace with real backend endpoint when available.
 */
export async function getSystemStatus(token) {
    // Try to check if backend is actually online
    try {
        const response = await fetch(`${API_BASE_URL}/files`, {
            method: 'HEAD',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        // If backend responds, return mock metrics
        // TODO: Replace with GET /system/status endpoint
        return {
            totalFiles: 42,
            totalStorage: '128.5 MB',
            uptime: '48h 32m',
            lastCheck: new Date().toISOString()
        };
    } catch (error) {
        // Backend is offline
        throw new Error('Backend offline');
    }
}

/**
 * Get activity logs (admin only)
 * @param {string} token - JWT token
 * @param {Object} filters - Optional filters
 * @param {number} filters.limit - Maximum number of logs
 * @param {string} filters.action - Filter by action type
 * @param {string} filters.userId - Filter by user ID
 */
export async function getActivityLogs(token, filters = {}) {
    const params = new URLSearchParams();

    if (filters.limit) params.append('limit', filters.limit);
    if (filters.action) params.append('action_filter', filters.action);
    if (filters.userId) params.append('user_id_filter', filters.userId);

    const response = await fetch(`${API_BASE_URL}/admin/logs?${params}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch activity logs');
    }

    return await response.json();
}


/**
 * Generate Ed25519 signature keys for user
 * @param {string} token - JWT token
 * @param {string} vaultPassword - User's vault password
 */
export async function generateSignatureKeys(token, vaultPassword) {
    const response = await fetch(`${API_BASE_URL}/auth/generate-signature-keys?vault_password=${encodeURIComponent(vaultPassword)}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate signature keys');
    }

    return await response.json();
}

/**
 * Register client-side generated public key
 * @param {string} token - JWT token
 * @param {string} publicKey - Base64-encoded public key
 */
export async function registerClientPublicKey(token, publicKey) {
    const response = await fetch(`${API_BASE_URL}/auth/register-client-public-key?public_key=${encodeURIComponent(publicKey)}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to register public key');
    }

    return await response.json();
}

/**
 * Get current user's signature keys
 * @param {string} token - JWT token
 */
export async function getMySignatureKeys(token) {
    const response = await fetch(`${API_BASE_URL}/auth/my-signature-keys`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get keys');
    }

    return await response.json();
}

/**
 * Verify file integrity without downloading
 * @param {string} fileId - File ID
 * @param {string} token - JWT token
 */
export async function verifyFileIntegrity(fileId, token) {
    const response = await fetch(`${API_BASE_URL}/files/${fileId}/verify-integrity`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to verify integrity');
    }

    return await response.json();
}
