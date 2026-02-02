-- Personal Key Vault Schema Migration
-- Add this table to store encrypted encryption keys for users
-- Run this in Supabase SQL Editor

-- Create user_vaults table
CREATE TABLE IF NOT EXISTS user_vaults (
    vault_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    file_id UUID REFERENCES files_metadata(file_id) ON DELETE CASCADE,
    key_label TEXT, -- User-friendly label (e.g., "Telemetry Report Jan 2026")
    encrypted_hex TEXT NOT NULL, -- Encryption key, encrypted with user's password-derived key
    salt TEXT NOT NULL, -- Salt for password-based encryption
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups by user_id
CREATE INDEX IF NOT EXISTS idx_user_vaults_user_id ON user_vaults(user_id);

-- Create index for faster lookups by file_id
CREATE INDEX IF NOT EXISTS idx_user_vaults_file_id ON user_vaults(file_id);

COMMENT ON TABLE user_vaults IS 'Stores encrypted file encryption keys for users, protected by password-derived encryption';
COMMENT ON COLUMN user_vaults.encrypted_hex IS 'AES-256-GCM encrypted hex key, encrypted using password-derived key';
COMMENT ON COLUMN user_vaults.salt IS 'Random salt used for PBKDF2 key derivation from password';
