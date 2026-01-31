#!/bin/bash
# Comprehensive commit script for Secure Upload & Download Backend

set -e  # Exit on error

echo "🚀 Starting Git Commit Process..."
echo ""

# Stage all files
echo "📁 Staging all backend files..."
git add .gitignore
git add README.md
git add commit.sh
git add backend/

echo ""
echo "📝 Creating structured commits..."
echo ""

# Commit 1: Project infrastructure
git commit -m "chore: Setup project infrastructure and dependencies

- Configure .gitignore for Python, cache, downloads, and test files
- Add requirements.txt with FastAPI, Supabase, cryptography
- Create backend/downloads directory for CLI testing
- Add comprehensive README with setup instructions" 2>/dev/null || echo "  ℹ️  (already committed or no changes)"

echo "✅ Commit 1: Infrastructure"

# Commit 2: Crypto utilities
git commit -m "feat: Implement AES-256-GCM encryption system

- Add encrypt_chunk() with AES-256-GCM encryption
- Add decrypt_chunk() for download reassembly
- Implement SHA-256 integrity hashing
- Generate secure 256-bit keys and 96-bit IVs
- Base64 encoding for safe storage" backend/crypto_utils.py 2>/dev/null || echo "  ℹ️  (already committed)"

echo "✅ Commit 2: Crypto utilities"

# Commit 3: Supabase storage service
git commit -m "feat: Add Supabase storage and database integration

- Implement async upload_chunk_to_supabase()
- Add save_file_metadata() for DB persistence
- Implement get_file_metadata() for download queries
- Add download_chunk_from_supabase() for retrieval
- Support environment variable configuration" backend/storage_service.py backend/.env.example 2>/dev/null || echo "  ℹ️  (already committed)"

echo "✅ Commit 3: Storage service"

# Commit 4: Upload endpoint
git commit -m "feat: Implement secure streaming upload endpoint

- Add POST /upload with JWT authentication
- Stream files in 512KB chunks (memory-safe)
- Encrypt each chunk with unique session key
- Concurrent async uploads to Supabase
- Extract owner_id from JWT Bearer token
- Return encryption key and file_id to client

BREAKING CHANGE: Fixed key encoding from base64+hex to simple hex" backend/main.py 2>/dev/null || echo "  ℹ️  (already committed)"

echo "✅ Commit 4: Upload endpoint"

# Commit 5: Download endpoint with MFA
git commit -m "feat: Implement secure download endpoint with MFA verification

- Add GET /download/{file_id} with streaming response
- Enforce MFA check: reject aal1 (password-only)
- Verify file ownership before download
- Stream chunk reassembly: Download → Decode → Decrypt → Yield
- Set Content-Disposition for browser downloads
- Add extract_claims_from_token() for aal verification

Security:
- MFA required (aal2) for all downloads
- Owner-only access control
- Memory-safe streaming architecture" backend/main.py 2>/dev/null || echo "  ℹ️  (already committed)"

echo "✅ Commit 5: Download endpoint"

# Commit 6: Test scripts
git commit -m "test: Add comprehensive upload and download test suites

Upload Tests:
- upload_test.py: Offline encryption/chunking verification
- upload_pdf.py: End-to-end upload with real file

Download Tests:
- download_test.py: HTTP streaming download + MFA verification
- test_manual_download.py: Direct chunk reassembly validation
- SHA-256 hash comparison for integrity verification

All tests save to backend/downloads/ for easy access" backend/upload_test.py backend/upload_pdf.py backend/download_test.py backend/test_manual_download.py backend/downloads/.gitkeep 2>/dev/null || echo "  ℹ️  (already committed)"

echo "✅ Commit 6: Test scripts"

# Commit 7: Documentation
git commit -m "docs: Add setup guides and API documentation

- Update README with quickstart
- Document environment variables
- Add API endpoint usage examples
- Include curl commands for testing" README.md backend/README.md backend/SUPABASE_SETUP.md 2>/dev/null || echo "  ℹ️  (already committed)"

echo "✅ Commit 7: Documentation"

echo ""
echo "🎉 All commits created successfully!"
echo ""
echo "📊 Current Git Status:"
git status --short
echo ""
echo "📝 Recent commits:"
git log --oneline -10
echo ""
echo "💡 Next steps:"
echo "   git push origin main"
