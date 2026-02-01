-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Files Metadata Table
-- Stores technical details and security metadata for uploaded files
CREATE TABLE IF NOT EXISTS files_metadata (
    file_id UUID PRIMARY KEY,
    owner_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    classification TEXT NOT NULL DEFAULT 'public', -- 'top_secret', 'mission_logs', 'public'
    total_chunks INTEGER NOT NULL,
    encryption_iv TEXT NOT NULL,
    chunk_hashes TEXT[], -- Array of SHA-256 hashes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Audit Logs Table
-- Immutable log of all access attempts (Success & Failure)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id TEXT NOT NULL,
    action TEXT NOT NULL, -- 'UPLOAD', 'DOWNLOAD', 'ACCESS_DENIED'
    resource_id TEXT,
    details JSONB, -- Stores flexible details like reason, IP, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optional: Create an index on specific columns for faster querying
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
