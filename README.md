# VAJRA 🔐

<div align="center">

![Security](https://img.shields.io/badge/Security-Zero--Trust-red?style=for-the-badge&logo=security)
![Encryption](https://img.shields.io/badge/Encryption-AES--256--GCM-blue?style=for-the-badge&logo=lock)
![Signatures](https://img.shields.io/badge/Signatures-Ed25519-green?style=for-the-badge&logo=key)
![Auth](https://img.shields.io/badge/Auth-Email--MFA-orange?style=for-the-badge&logo=shield)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Zero-Trust, Quantum-Resistant File Sharing System for Satellite Telemetry Data**

[Features](#-key-features) • [Security](#-security-implementation) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Documentation](#-documentation)

</div>

---

## 📖 Overview

**VAJRA** is a military-grade secure file sharing system designed for satellite telemetry data exchange with enterprise-level security. Built on Zero-Trust principles, it ensures end-to-end encryption, cryptographic integrity verification, and role-based access control.

### Why VAJRA?

- ✅ **Zero-Trust Architecture** - Never trust, always verify
- ✅ **Quantum-Resistant Crypto** - Future-proof security with Ed25519
- ✅ **End-to-End Encryption** - AES-256-GCM for all data
- ✅ **Digital Signatures** - Cryptographic integrity verification
- ✅ **Multi-Factor Authentication** - Email-based MFA for all users
- ✅ **Role-Based Access Control** - Admin, Operator, Engineer clearance levels

---

## 🔐 Security Implementation

### Encryption & Protection

| Technology | Purpose | Implementation |
|------------|---------|----------------|
| **AES-256-GCM** | File encryption | All files split into 1MB chunks, each encrypted individually |
| **Ed25519** | Digital signatures | Cryptographic signing for file integrity verification |
| **SHA-256** | Hash functions | Chunk integrity verification and tamper detection |
| **PBKDF2** | Key derivation | 100,000 iterations for vault password encryption |
| **Chunked Storage** | Data fragmentation | 1MB encrypted chunks prevent full file reconstruction |

### Authentication & Access

- **🔒 Email-Based MFA** - Two-factor authentication via 6-digit email codes
- **🔒 JWT Tokens** - Secure session management with token-based auth
- **🔒 Role-Based Access Control (RBAC)** - Three clearance levels:
  - **Admin** - Full system access, user management, audit logs
  - **Operator** - Upload/download files, view mission logs
  - **Engineer** - Read-only access to public files
- **🔒 Supabase Authentication** - Enterprise-grade auth infrastructure

### Data Protection

- **🛡️ Zero-Trust Design** - All requests authenticated and authorized
- **🛡️ Secure HTTP Headers** - Sensitive data transmitted via headers (X-Vault-Password, X-Public-Key), NOT URL parameters
- **🛡️ Row-Level Security** - Database policies enforce user isolation
- **🛡️ Encrypted Storage** - All data encrypted at rest in Supabase
- **🛡️ Client-Side Encryption** - Files encrypted before upload
- **🛡️ No Plaintext Storage** - Original files never stored unencrypted

### Audit & Compliance

- **📝 Immutable Audit Logs** - All actions tracked with timestamps
- **📝 Integrity Verification** - Pre-download integrity checks with detailed reports
- **📝 Digital Signatures** - File authenticity verification via Ed25519
- **📝 Classification Levels** - Public, Mission Logs, Top Secret data separation
- **📝 Forensic Capabilities** - Signature validation and tamper detection

---

## ✨ Key Features

### 🔑 Vault Key Management
- Store multiple vault keys with custom labels
- Reuse keys for quick downloads without re-entering passwords
- Encrypted storage with PBKDF2 key derivation
- QR code generation for public key sharing

### 📂 File Operations
- **Upload**: AES-256-GCM encryption, optional Ed25519 signing
- **Download**: Automatic chunk reassembly and decryption
- **Integrity Check**: Verify chunks and signatures before download
- **Pagination**: Clean interface showing 10 files per page

### 🔍 Real-Time Monitoring
- Live file count and storage statistics
- Chunk-level integrity status
- Signature verification results
- User activity tracking

### 🎨 Modern UI
- Neo-Brutalism design language
- Responsive React interface
- Real-time feedback and notifications
- Accessible and intuitive navigation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      VAJRA SYSTEM                           │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   FRONTEND       │         │    BACKEND       │         │   SUPABASE       │
│   React + Vite   │◄───────►│   FastAPI        │◄───────►│  PostgreSQL      │
│                  │  HTTPS  │   Python 3.x     │  API    │  Storage         │
│  • Neo-Brutal UI │         │                  │         │  Auth            │
│  • Client Crypto │         │  • AES-256-GCM   │         │  • Row-Level Sec │
│  • Secure Headers│         │  • Ed25519       │         │  • MFA           │
│  • JWT Auth      │         │  • JWT Verify    │         │  • Encrypted DB  │
└──────────────────┘         │  • RBAC          │         └──────────────────┘
                              │  • Chunking      │
                              └──────────────────┘
```

### Tech Stack

**Frontend**
- React 19.2.0
- Vite 7.2.4
- TailwindCSS 4.1.18
- Lucide React (icons)
- QRCode.js (QR generation)

**Backend**
- FastAPI 0.109.0
- Python 3.x
- Cryptography 41.0.7 (AES, Ed25519)
- Uvicorn (ASGI server)

**Infrastructure**
- Supabase (Auth + Storage + Database)
- PostgreSQL (metadata)
- Email service (Nodemailer for MFA)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** - Backend runtime
- **Node.js 18+** - Frontend development
- **Supabase Account** - Database and storage
- **Email SMTP** - For MFA codes

### 1. Clone Repository

```bash
git clone <repository-url>
cd vajra
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials
```

**Environment Variables** (`.env`):
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

**Database Setup** (Run in Supabase SQL Editor):
```sql
-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'operator', 'engineer')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Files metadata
CREATE TABLE files_metadata (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES users(user_id),
    filename TEXT NOT NULL,
    classification TEXT NOT NULL,
    total_chunks INTEGER NOT NULL,
    file_signature TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- File chunks
CREATE TABLE file_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files_metadata(file_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    encrypted_data BYTEA NOT NULL,
    encryption_iv TEXT NOT NULL,
    chunk_signature TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vault keys
CREATE TABLE vault_keys (
    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    key_label TEXT NOT NULL,
    encrypted_vault_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User signature keys
CREATE TABLE user_signature_keys (
    user_id UUID PRIMARY KEY REFERENCES users(user_id),
    public_key TEXT NOT NULL,
    encrypted_private_key TEXT,
    storage_method TEXT NOT NULL,
    algorithm TEXT NOT NULL DEFAULT 'ed25519',
    keys_generated_at TIMESTAMP DEFAULT NOW()
);
```

**Start Backend**:
```bash
uvicorn main:app --reload
# API available at http://localhost:8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# UI available at http://localhost:5173
```

### 4. Configure Email MFA

Create `send-email.js` in the root directory for MFA functionality:
```javascript
// Configure with your SMTP credentials (Gmail, SendGrid, etc.)
```

---

## 📚 Documentation

### User Flow

1. **Authentication**
   - Enter email & password
   - Receive 6-digit MFA code via email
   - Verify code to obtain JWT token

2. **Key Generation**
   - Navigate to "GEN KEYS"
   - Create vault password
   - Backend generates Ed25519 key pair
   - Private key encrypted with vault password
   - Public key registered for signing

3. **File Upload**
   - Select classification (Public/Mission Logs/Top Secret)
   - Choose file
   - Optionally provide vault password for signing
   - File split into 1MB chunks
   - Each chunk encrypted with AES-256-GCM
   - Optional: File hash signed with private key
   - Chunks stored in database

4. **File Access**
   - View files in "VAULT"
   - Paginated list (10 files/page)
   - See file details (name, classification, chunks, owner)

5. **Integrity Check**
   - Click "CHECK" button
   - Backend verifies chunk integrity and signature
   - Shows detailed results (chunk status, signature verification)
   - Indicates if file is safe to download

6. **File Download**
   - **KEY Method**: Select stored vault key → Decrypt private key → Download
   - **Manual Method**: Enter vault password → Download
   - Backend reassembles and decrypts chunks
   - Original file reconstructed and downloaded

### API Endpoints

#### Authentication
- `POST /login` - User login with email/password
- `POST /verify-mfa` - Verify MFA code
- `GET /verify-token` - Validate JWT token

#### Key Management
- `POST /auth/generate-signature-keys` - Generate Ed25519 keys
- `POST /auth/register-client-public-key` - Register public key
- `GET /auth/my-signature-keys` - Retrieve user's keys

#### File Operations
- `POST /upload` - Upload encrypted file
- `GET /files` - List user's files (paginated)
- `GET /download/{file_id}` - Download and decrypt file
- `POST /verify/{file_id}` - Verify file integrity

#### Vault Keys
- `POST /vault-keys` - Store vault key
- `GET /vault-keys` - List user's vault keys
- `DELETE /vault-keys/{key_id}` - Delete vault key

---

## 🔒 Security Best Practices

### For Developers

1. **Never log sensitive data** - Vault passwords, private keys, tokens
2. **Use HTTPS in production** - Encrypt all network traffic
3. **Rotate JWT secrets** - Regularly update signing keys
4. **Enable rate limiting** - Prevent brute-force attacks
5. **Monitor audit logs** - Track suspicious activity

### For Users

1. **Use strong vault passwords** - Minimum 12 characters, mixed case, symbols
2. **Never share private keys** - Keep them secure and offline
3. **Verify file integrity** - Always run integrity checks before download
4. **Use stored vault keys** - Avoid re-entering passwords frequently
5. **Report suspicious activity** - Contact admin immediately

---

## 📊 Project Status

- ✅ **Authentication** - Email MFA, JWT tokens, RBAC
- ✅ **Encryption** - AES-256-GCM for files
- ✅ **Digital Signatures** - Ed25519 signing and verification
- ✅ **File Operations** - Upload, download, chunking
- ✅ **Vault Management** - Key storage and retrieval
- ✅ **Integrity Checks** - Pre-download verification
- ✅ **Frontend UI** - Complete Neo-Brutalism interface
- ✅ **QR Code Sharing** - Public key QR generation

---

## 🤝 Contributing

This is a security-focused project. Before contributing:

1. Read the codebase documentation
2. Follow secure coding practices
3. Test all security features
4. Submit detailed pull requests

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👥 Support

For security issues, please contact the security team directly. Do not open public issues for security vulnerabilities.

---

<div align="center">

**Built with 🔐 by the VAJRA Team**

*Zero-Trust • Quantum-Resistant • Military-Grade Security*

</div>
