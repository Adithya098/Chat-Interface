-- One-time PostgreSQL migration: S3 columns -> Supabase Storage columns.
-- Safe if already migrated or created with the new schema (skips missing columns).

ALTER TABLE documents ADD COLUMN IF NOT EXISTS storage_bucket VARCHAR(255);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS storage_path VARCHAR(1024);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS storage_public_url TEXT;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'documents' AND column_name = 's3_key'
  ) THEN
    UPDATE documents SET storage_path = s3_key WHERE storage_path IS NULL AND s3_key IS NOT NULL;
  END IF;
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'documents' AND column_name = 's3_url'
  ) THEN
    UPDATE documents SET storage_public_url = s3_url WHERE storage_public_url IS NULL AND s3_url IS NOT NULL;
  END IF;
END $$;

ALTER TABLE documents DROP COLUMN IF EXISTS s3_url;
ALTER TABLE documents DROP COLUMN IF EXISTS s3_key;
