-- Migration: Add per_source_details column to scan_history
ALTER TABLE scan_history ADD COLUMN per_source_details TEXT DEFAULT '[]';

-- Update existing records to have empty array
UPDATE scan_history SET per_source_details = '[]' WHERE per_source_details IS NULL;