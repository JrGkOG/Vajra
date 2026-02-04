-- Add key storage method column to users table
-- Supports both password-encrypted and client-side file-based keys

ALTER TABLE users ADD COLUMN IF NOT EXISTS key_storage_method VARCHAR(20) DEFAULT 'password';
-- Values: 'password' (encrypted with vault password) or 'client_file' (user manages key file)

-- Add constraint to ensure valid values
ALTER TABLE users ADD CONSTRAINT key_storage_method_check 
    CHECK (key_storage_method IN ('password', 'client_file'));

-- For 'client_file' method, signature_private_key_encrypted will be NULL
-- For 'password' method, signature_private_key_encrypted contains encrypted key

-- Add comment
COMMENT ON COLUMN users.key_storage_method IS 'Key storage method: password (server-stored encrypted) or client_file (user manages key file)';

-- Migration for existing users: default to 'password' method
UPDATE users 
SET key_storage_method = 'password' 
WHERE signature_public_key IS NOT NULL 
  AND key_storage_method IS NULL;
