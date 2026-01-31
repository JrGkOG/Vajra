"""
Storage service for interacting with Supabase Storage and Database.
Handles async chunk uploads and metadata persistence.
"""

import os
from typing import Dict, Any
from supabase import create_client, Client
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Supabase client
# These environment variables must be set: SUPABASE_URL, SUPABASE_KEY
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing required environment variables: SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def upload_chunk_to_supabase(bucket: str, path: str, data: str) -> Dict[str, Any]:
    """
    Upload a Base64-encoded encrypted chunk to Supabase Storage.
    
    Args:
        bucket: Supabase storage bucket name (e.g., 'uploads')
        path: Storage path for the chunk (e.g., '/uploads/{file_id}/chunk_{index}')
        data: Base64-encoded encrypted chunk data
    
    Returns:
        dict: Response from Supabase Storage API
    
    Raises:
        Exception: If upload fails
    """
    try:
        # Convert base64 string back to bytes for upload
        # The supabase-py library's storage.upload expects bytes
        chunk_bytes = data.encode('utf-8')
        
        # Upload to Supabase Storage
        # Note: supabase.storage.from_(bucket).upload() is synchronous
        # For true async, we'd use httpx directly with Supabase Storage API
        # For now, we'll use the sync method in an async function
        # (In production, consider using httpx for async uploads)
        
        response = supabase.storage.from_(bucket).upload(
            path=path,
            file=chunk_bytes,
            file_options={"content-type": "application/octet-stream"}
        )
        
        return {"success": True, "path": path, "response": response}
    
    except Exception as e:
        # If upload fails, we abort the entire process (per requirements)
        raise Exception(f"Failed to upload chunk to path {path}: {str(e)}")


async def save_file_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert file metadata record into Supabase 'files_metadata' table.
    
    Args:
        metadata: Dictionary containing:
            - file_id (str): UUID of the file
            - owner_id (str): User ID from JWT token
            - filename (str): Original filename
            - total_chunks (int): Number of chunks
            - encryption_iv (str): Base64-encoded IV used for encryption
            - chunk_hashes (list, optional): List of SHA-256 hashes for each chunk
    
    Returns:
        dict: Inserted record from database
    
    Raises:
        Exception: If database insert fails
    """
    try:
        # Insert into files_metadata table
        # Note: Ensure the table exists with appropriate schema:
        # CREATE TABLE files_metadata (
        #     file_id UUID PRIMARY KEY,
        #     owner_id TEXT NOT NULL,
        #     filename TEXT NOT NULL,
        #     total_chunks INTEGER NOT NULL,
        #     encryption_iv TEXT NOT NULL,
        #     chunk_hashes TEXT[],
        #     created_at TIMESTAMP DEFAULT NOW()
        # );
        
        response = supabase.table("files_metadata").insert(metadata).execute()
        
        return {"success": True, "data": response.data}
    
    except Exception as e:
        raise Exception(f"Failed to save metadata to database: {str(e)}")
