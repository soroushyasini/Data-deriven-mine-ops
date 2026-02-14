-- Create metabase database for Metabase internal storage
-- Only creates if it doesn't exist (safe for re-runs)
SELECT 'CREATE DATABASE metabase' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metabase')\gexec

