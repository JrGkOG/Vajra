# Vajra - Secure File Upload System

A secure file upload system with AES-256-GCM encryption, sharding, and Supabase integration.

## 📁 Project Structure

```
vajra/
├── backend/          # FastAPI backend with encryption & sharding
│   ├── main.py
│   ├── crypto_utils.py
│   ├── storage_service.py
│   ├── test_upload.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/         # Frontend application (to be implemented)
└── README.md
```

## 🚀 Quick Start

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Supabase**
   
   Copy the environment template:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Supabase credentials:
   - `SUPABASE_URL`: Your project URL from Supabase Dashboard
   - `SUPABASE_KEY`: Your API key (anon or service_role)
   
   **How to get these values:**
   - Go to [Supabase Dashboard](https://app.supabase.com)
   - Select your project → Settings → API
   - Copy "Project URL" and "anon public" key

4. **Set up Supabase Storage & Database**
   
   Create a storage bucket named `uploads` (make it private)
   
   Create the metadata table:
   ```sql
   CREATE TABLE files_metadata (
       file_id UUID PRIMARY KEY,
       owner_id TEXT NOT NULL,
       filename TEXT NOT NULL,
       total_chunks INTEGER NOT NULL,
       encryption_iv TEXT NOT NULL,
       chunk_hashes TEXT[],
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

5. **Test the encryption flow**
   ```bash
   python3 test_upload.py
   ```

6. **Start the server**
   ```bash
   uvicorn main:app --reload
   ```

7. **Test upload endpoint**
   ```bash
   curl -X POST "http://localhost:8000/upload" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "file=@sample.pdf"
   ```

## 🔐 What You Need

### Required Supabase Configuration

| Variable | Description | Where to Find |
|----------|-------------|---------------|
| `SUPABASE_URL` | Your project URL | Dashboard → Settings → API → Project URL |
| `SUPABASE_KEY` | API Key (anon or service_role) | Dashboard → Settings → API → Project API keys |

### Supabase Setup Checklist

- [ ] Create a Supabase project at [supabase.com](https://supabase.com)
- [ ] Create storage bucket `uploads` (Settings → Storage)
- [ ] Create `files_metadata` table (SQL Editor)
- [ ] Copy URL and API key to `.env` file

## 📚 Documentation

For detailed documentation, see the [Backend README](backend/README.md).

## 🏗️ Architecture

- **Backend**: FastAPI with AES-256-GCM encryption, 512KB chunking, async uploads
- **Storage**: Supabase Storage for encrypted chunks
- **Database**: Supabase PostgreSQL for metadata
- **Frontend**: To be implemented

## 📝 License

MIT
