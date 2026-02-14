-- Create metabase database for Metabase internal storage
SELECT 'CREATE DATABASE metabase' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metabase')\gexec
