-- Add the 'classification' column to the existing files_metadata table
-- Run this SQL in your Supabase SQL Editor

ALTER TABLE files_metadata 
ADD COLUMN IF NOT EXISTS classification TEXT NOT NULL DEFAULT 'public';

-- Add a check constraint to ensure valid classification values
ALTER TABLE files_metadata
ADD CONSTRAINT classification_check 
CHECK (classification IN ('top_secret', 'mission_logs', 'public'));

-- Optional: Update existing rows to have the default classification
UPDATE files_metadata 
SET classification = 'public' 
WHERE classification IS NULL;
