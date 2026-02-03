-- Users table with role-based access control
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'engineer', 'staff')),
    can_upload BOOLEAN DEFAULT true,
    can_download BOOLEAN DEFAULT true,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'inactive')),
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID REFERENCES users(user_id),
    last_login TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Role permissions reference (for documentation)
-- admin:    Full access - can create users, view logs, upload, download all files
-- manager:  Can upload, download own files + team files, view team logs
-- engineer: Can upload, download own files
-- staff:    Can download own files only (no upload by default)

-- Insert default users for testing (CHANGE PASSWORDS IN PRODUCTION!)
-- Password hashes generated with bcrypt (rounds=12)

-- Admin user (email: admin@vajra.mil, password: 'admin123')
INSERT INTO users (email, username, password_hash, role, can_upload, can_download, status)
VALUES (
    'admin@vajra.mil',
    'admin',
    '$2b$12$DuNb08jIqmmJUrEXQOn4x.WYiCWjUMB/mm098aOF8SWawa5Jgwzea',
    'admin',
    true,
    true,
    'active'
)
ON CONFLICT (email) DO NOTHING;

-- Manager user (email: manager@vajra.mil, password: 'manager123')
INSERT INTO users (email, username, password_hash, role, can_upload, can_download, status)
VALUES (
    'manager@vajra.mil',
    'manager',
    '$2b$12$jNZSLHk47a8S0VVoFc/2.OqB/wv6JD296NL0qZDMn8L6744KNWgUC',
    'manager',
    true,
    true,
    'active'
)
ON CONFLICT (email) DO NOTHING;

-- Engineer user (email: engineer@vajra.mil, password: 'engineer123')
INSERT INTO users (email, username, password_hash, role, can_upload, can_download, status)
VALUES (
    'engineer@vajra.mil',
    'engineer',
    '$2b$12$awZbQbxAJxGs28umdSg9KuTe9G2h6Bl8JhpnRCvHwPplNr31IzbMO',
    'engineer',
    true,
    true,
    'active'
)
ON CONFLICT (email) DO NOTHING;

-- Staff user (email: staff@vajra.mil, password: 'staff123')
INSERT INTO users (email, username, password_hash, role, can_upload, can_download, status)
VALUES (
    'staff@vajra.mil',
    'staff',
    '$2b$12$dE41OHoLHpjp6gtA3FT6vuhpRAdfjAvF7YwSPNQZS.G7QWUMw8pRC',
    'staff',
    false,  -- Staff cannot upload by default
    true,   -- Staff can download
    'active'
)
ON CONFLICT (email) DO NOTHING;

-- Activity logs table for audit trail
CREATE TABLE IF NOT EXISTS activity_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details JSONB,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT now()
);

-- Create index for faster log queries
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);

-- MFA codes table (temporary storage for email verification codes)
CREATE TABLE IF NOT EXISTS mfa_codes (
    code_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    email TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    purpose TEXT NOT NULL CHECK (purpose IN ('login', 'vault_store', 'vault_retrieve')),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create index for faster MFA code lookups
CREATE INDEX IF NOT EXISTS idx_mfa_codes_email ON mfa_codes(email);
CREATE INDEX IF NOT EXISTS idx_mfa_codes_user ON mfa_codes(user_id);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to update updated_at on users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts with role-based access control';
COMMENT ON TABLE activity_logs IS 'Audit trail for all user actions';
COMMENT ON TABLE mfa_codes IS 'Temporary storage for email-based MFA codes';
COMMENT ON COLUMN users.role IS 'User role: admin > manager > engineer > staff (decreasing priority)';
COMMENT ON COLUMN users.can_upload IS 'Permission to upload files';
COMMENT ON COLUMN users.can_download IS 'Permission to download files';
