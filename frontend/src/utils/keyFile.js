/**
 * Manual-mode key files.
 *
 * When a user uploads without saving the key to the vault, the encryption key
 * is written to a numbered .txt file instead of being shown on screen. To
 * download the file later they hand that .txt back and the key is read from it.
 */

const COUNTER_KEY = 'vajra_key_counter';
const HEX_KEY = /\b[0-9a-fA-F]{64}\b/;                 // AES-256 key = 32 bytes = 64 hex chars
const FILE_ID = /File ID:\s*([0-9a-fA-F-]{36})/;
const KEY_NO = /Key No:\s*(\d+)/;

/** Next sequence number (per browser). Falls back to a timestamp if storage is blocked. */
export function nextKeyNumber() {
    try {
        const next = (parseInt(localStorage.getItem(COUNTER_KEY) || '0', 10) || 0) + 1;
        localStorage.setItem(COUNTER_KEY, String(next));
        return String(next).padStart(4, '0');
    } catch {
        return String(Date.now()).slice(-6);
    }
}

export function buildKeyFile({ number, filename, fileId, keyHex }) {
    return [
        'VAJRA ENCRYPTION KEY',
        '====================',
        `Key No: ${number}`,
        `File: ${filename}`,
        `File ID: ${fileId}`,
        '',
        'Key (hex):',
        keyHex,
        '',
        'Keep this file safe. Anyone holding it can decrypt the file above.',
        'To download the file later, choose DL and select this key file.',
        '',
    ].join('\n');
}

/**
 * Pull the key out of an uploaded key file. Accepts the full Vajra key file or
 * a bare 64-character hex string. Returns null when no key is present.
 */
export function parseKeyFile(text) {
    const key = (text || '').match(HEX_KEY);
    if (!key) return null;
    return {
        key: key[0].toLowerCase(),
        fileId: (text.match(FILE_ID) || [])[1] || null,
        number: (text.match(KEY_NO) || [])[1] || null,
    };
}

/** Trigger a browser download of a text file. */
export function downloadTextFile(name, text) {
    const url = URL.createObjectURL(new Blob([text], { type: 'text/plain' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const keyFileName = (number) => `vajra-key-${number}.txt`;
