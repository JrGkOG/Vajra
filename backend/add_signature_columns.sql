-- Add digital signature columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS signature_public_key TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS signature_private_key_encrypted TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS signature_algorithm TEXT DEFAULT 'ed25519';
ALTER TABLE users ADD COLUMN IF NOT EXISTS signature_keys_generated_at TIMESTAMPTZ;

-- Add digital signature columns to files_metadata table
ALTER TABLE files_metadata ADD COLUMN IF NOT EXISTS chunk_signatures TEXT[];
ALTER TABLE files_metadata ADD COLUMN IF NOT EXISTS file_signature TEXT;
ALTER TABLE files_metadata ADD COLUMN IF NOT EXISTS signature_algorithm TEXT DEFAULT 'ed25519';
ALTER TABLE files_metadata ADD COLUMN IF NOT EXISTS signed_by_user_id TEXT;

-- Add indexes for signature queries
CREATE INDEX IF NOT EXISTS idx_files_metadata_signed_by ON files_metadata(signed_by_user_id);

-- Add comments for documentation
COMMENT ON COLUMN users.signature_public_key IS 'Base64-encoded Ed25519 public key for signature verification';
COMMENT ON COLUMN users.signature_private_key_encrypted IS 'Private key encrypted with user vault password';
COMMENT ON COLUMN files_metadata.chunk_signatures IS 'Array of Ed25519 signatures, one per chunk';
COMMENT ON COLUMN files_metadata.file_signature IS 'Ed25519 signature over file manifest (metadata)';
COMMENT ON COLUMN files_metadata.signed_by_user_id IS 'User ID who uploaded and signed the file';
