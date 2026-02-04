/**
 * Client-side cryptographic key generation utilities
 * For generating Ed25519 signature keys in the browser
 */

/**
 * Generate Ed25519 key pair in the browser
 * @returns {Promise<{publicKey: string, privateKey: string}>}
 */
export async function generateEd25519KeyPair() {
    // Generate Ed25519 key pair using Web Crypto API
    const keyPair = await window.crypto.subtle.generateKey(
        {
            name: "Ed25519",
        },
        true, // extractable
        ["sign", "verify"]
    );

    // Export public key to SPKI format (PEM)
    const publicKeyBuffer = await window.crypto.subtle.exportKey("spki", keyPair.publicKey);
    const publicKeyBase64 = bufferToBase64(publicKeyBuffer);

    // Export private key to PKCS8 format (PEM)
    const privateKeyBuffer = await window.crypto.subtle.exportKey("pkcs8", keyPair.privateKey);
    const privateKeyBase64 = bufferToBase64(privateKeyBuffer);

    return {
        publicKey: publicKeyBase64,
        privateKey: privateKeyBase64
    };
}

/**
 * Import Ed25519 private key from base64 string
 * @param {string} privateKeyBase64 
 * @returns {Promise<CryptoKey>}
 */
export async function importPrivateKey(privateKeyBase64) {
    const privateKeyBuffer = base64ToBuffer(privateKeyBase64);

    return await window.crypto.subtle.importKey(
        "pkcs8",
        privateKeyBuffer,
        {
            name: "Ed25519",
        },
        true,
        ["sign"]
    );
}

/**
 * Sign data with Ed25519 private key
 * @param {string} data - Data to sign (will be converted to UTF-8)
 * @param {CryptoKey} privateKey - Ed25519 private key
 * @returns {Promise<string>} Base64-encoded signature
 */
export async function signData(data, privateKey) {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);

    const signature = await window.crypto.subtle.sign(
        {
            name: "Ed25519",
        },
        privateKey,
        dataBuffer
    );

    return bufferToBase64(signature);
}

/**
 * Download private key as a file
 * @param {string} privateKeyBase64 - Base64-encoded private key
 * @param {string} filename - Filename for download
 */
export function downloadPrivateKey(privateKeyBase64, filename = 'vajra_private_key.pem') {
    // Convert to PEM format
    const pemKey = `-----BEGIN PRIVATE KEY-----\n${formatBase64(privateKeyBase64)}\n-----END PRIVATE KEY-----`;

    const blob = new Blob([pemKey], { type: 'application/x-pem-file' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();

    URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

/**
 * Read private key from uploaded file
 * @param {File} file - PEM file
 * @returns {Promise<string>} Base64-encoded private key (without PEM headers)
 */
export async function readPrivateKeyFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onload = (e) => {
            try {
                let pemContent = e.target.result;

                // Remove PEM headers and whitespace
                pemContent = pemContent
                    .replace('-----BEGIN PRIVATE KEY-----', '')
                    .replace('-----END PRIVATE KEY-----', '')
                    .replace(/\s/g, '');

                resolve(pemContent);
            } catch (error) {
                reject(new Error('Invalid private key file'));
            }
        };

        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

// Utility functions

function bufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

function base64ToBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
}

function formatBase64(base64, lineLength = 64) {
    // Format base64 string with line breaks for PEM format
    const lines = [];
    for (let i = 0; i < base64.length; i += lineLength) {
        lines.push(base64.substring(i, i + lineLength));
    }
    return lines.join('\n');
}
