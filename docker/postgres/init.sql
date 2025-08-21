-- PostgreSQL initialization script for Salient development environment
-- This script runs automatically when the postgres container starts for the first time

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create additional development users if needed
-- (The main salient_user is already created via environment variables)

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE salient_dev TO salient_user;

-- Set up any initial development data or configurations
-- (This will be expanded as needed during Epic 0004 implementation)

-- Log successful initialization
SELECT 'Salient development database initialized successfully' AS status;
