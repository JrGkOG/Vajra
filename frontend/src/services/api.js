/**
 * API Service Layer for communicating with the FastAPI backend.
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Login user and get JWT token
 * @param {string} username 
 * @param {string} password 
 * @returns {Promise<{access_token: string, user: object}>}
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
export async function uploadFile(file, classification, token) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload?classification=${classification}`, {
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
        throw new Error(error.detail ||'Failed to store key in vault');
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
