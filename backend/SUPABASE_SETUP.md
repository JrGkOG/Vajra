# SUPABASE SETUP GUIDE

## What You Need to Configure

To run the backend, you need **2 things from Supabase**:

### 1. SUPABASE_URL
Your unique project URL

### 2. SUPABASE_KEY  
Your API authentication key

---

## How to Get These Values

### Step 1: Go to Supabase Dashboard
👉 [https://app.supabase.com](https://app.supabase.com)

### Step 2: Select Your Project
If you don't have a project yet, create one (it's free).

### Step 3: Navigate to Settings → API
1. Click on **Settings** (gear icon) in the left sidebar
2. Click on **API**

### Step 4: Copy Your Credentials

You'll see two important values:

#### Project URL
```
https://xxxxxxxxxxxxx.supabase.co
```
☝️ Copy this entire URL → This is your `SUPABASE_URL`

#### API Keys
You'll see two keys:
- **anon public** - For client-side applications (safe to expose)
- **service_role** - For server-side applications (keep secret)

For this backend, use either:
- `anon public` if you want row-level security
- `service_role` for full admin access (recommended for backend)

☝️ Copy one of these keys → This is your `SUPABASE_KEY`

---

## Configuration Steps

### 1. Create `.env` file
```bash
cd backend
cp .env.example .env
```

### 2. Edit `.env` file
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-actual-key-here
```

Replace:
- `https://your-project-id.supabase.co` with your actual Project URL
- `your-actual-key-here` with your anon or service_role key

---

## Supabase Storage & Database Setup

### Create Storage Bucket

1. Go to **Storage** in Supabase Dashboard
2. Click "**New bucket**"
3. Name it: `uploads`
4. Set as **Private** (not public)
5. Click "Create bucket"

### Create Database Table

1. Go to **SQL Editor** in Supabase Dashboard
2. Click "**New query**"    
3. Paste this SQL:

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

4. Click "**Run**"

---

## ✅ Verification

Once configured, test your setup:

```bash
cd backend
python3 test_upload.py
```

If successful, you'll see:
```
✅ ALL TESTS PASSED
```

---

## 🔒 Security Notes

- **Never commit `.env` to git** (it's already in `.gitignore`)
- Use `service_role` key only on the server (never expose to frontend)
- Keep your keys secure and rotate them periodically

---

## Need Help?

If you get errors:
1. Double-check your URL has `https://` prefix
2. Ensure there are no extra spaces in your `.env` file
3. Verify the bucket `uploads` exists in Supabase Storage
4. Verify the table `files_metadata` exists in your database
