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


async def get_file_metadata(file_id: str) -> Dict[str, Any]:
    """
    Retrieve file metadata from Supabase database.
    
    Args:
        file_id: UUID of the file to retrieve metadata for
    
    Returns:
        dict: File metadata containing:
            - file_id (str)
            - owner_id (str)
            - filename (str)
            - total_chunks (int)
            - encryption_iv (str)
            - chunk_hashes (list)
            - created_at (timestamp)
    
    Raises:
        Exception: If file not found or database query fails
    """
    try:
        response = supabase.table("files_metadata").select("*").eq("file_id", file_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise Exception(f"File not found: {file_id}")
        
        return response.data[0]
    
    except Exception as e:
        raise Exception(f"Failed to retrieve file metadata: {str(e)}")


async def download_chunk_from_supabase(bucket: str, path: str) -> str:
    """
    Download an encrypted chunk from Supabase Storage.
    
    Args:
        bucket: Supabase storage bucket name (e.g., 'uploads')
        path: Storage path for the chunk (e.g., '{file_id}/chunk_{index}')
    
    Returns:
        str: Base64-encoded encrypted chunk data
    
    Raises:
        Exception: If download fails or chunk not found
    """
    try:
        # Download from Supabase Storage
        response = supabase.storage.from_(bucket).download(path)
        
        if not response:
            raise Exception(f"Chunk not found at path: {path}")
        
        # The response is bytes, decode to string (Base64)
        chunk_data = response.decode('utf-8')
        
        return chunk_data
    
    except Exception as e:
        raise Exception(f"Failed to download chunk from path {path}: {str(e)}")


async def log_audit_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log a security event to the audit_logs table.
    
    Args:
        event: Dictionary containing:
            - timestamp (str, ISO format)
            - user_id (str)
            - action (str): UPLOAD, DOWNLOAD, ACCESS_DENIED
            - resource_id (str): file_id
            - details (dict): Additional context (IP, reason, attributes)
            
    Returns:
        dict: Inserted record
        
    Note: Ensure 'audit_logs' table exists in Supabase.
    """
    try:
        # In a real app, you might want to fire-and-forget this or use a queue
        # so it doesn't block the main request. For PoC, we await it.
        response = supabase.table("audit_logs").insert(event).execute()

        # Mirror into the hash-chained ledger (tamper-evident; head anchored on-chain)
        from ledger_service import append_entry
        await append_entry(
            source="audit_logs",
            user_id=event.get("user_id"),
            action=event.get("action"),
            resource_id=event.get("resource_id"),
            details=event.get("details"),
        )
        return {"success": True, "data": response.data}
    except Exception as e:
        # Fail open or closed? For logging, usually fail open (log error but don't stop user)
        # But for high security, maybe fail closed.
        # We will just print/log the error here to avoid breaking user flow.
        print(f"⚠️ AUDIT LOGGING FAILED: {str(e)}")
        return {"success": False, "error": str(e)}


async def list_files() -> list:
    """
    List all files from the files_metadata table.
    
    Returns:
        list: List of file metadata dictionaries
    """
    try:
        response = supabase.table("files_metadata").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Failed to list files: {str(e)}")
        raise e

# Vault Operations

async def store_vault_key(vault_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store an encrypted key in the user_vaults table."""
    try:
        response = supabase.table("user_vaults").insert(vault_data).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise Exception(f"Failed to store vault key: {str(e)}")


async def retrieve_vault_key(vault_id: str, user_id: str) -> Dict[str, Any]:
    """Retrieve an encrypted key from user_vaults table."""
    try:
        response = supabase.table("user_vaults").select("*").eq("vault_id", vault_id).eq("user_id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise Exception(f"Vault key not found or access denied")
        
        return response.data[0]
    except Exception as e:
        raise Exception(f"Failed to retrieve vault key: {str(e)}")


async def list_vault_keys(user_id: str) -> list:
    """List all vault keys for a user (without decrypted values)."""
    try:
        response = supabase.table("user_vaults").select("vault_id, file_id, key_label, created_at").eq("user_id", user_id).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Failed to list vault keys: {str(e)}")
        raise e


async def delete_vault_key(vault_id: str, user_id: str) -> Dict[str, Any]:
    """Delete a vault key entry."""
    try:
        # First verify ownership
        response = supabase.table("user_vaults").select("user_id").eq("vault_id", vault_id).execute()
        
        if not response.data or response.data[0]['user_id'] !=user_id:
            raise Exception("Vault key not found or access denied")
        
        # Delete the entry
        supabase.table("user_vaults").delete().eq("vault_id", vault_id).execute()
        
        return {"success": True, "message": "Vault key deleted"}
    except Exception as e:
        raise Exception(f"Failed to delete vault key: {str(e)}")
