-- Initialize PostgreSQL for NASA APOD Pipeline
-- This script creates the apod_db database and necessary tables

-- Create the apod_db database
CREATE DATABASE apod_db OWNER postgres ENCODING 'UTF8' LC_COLLATE 'en_US.utf8' LC_CTYPE 'en_US.utf8' TEMPLATE template0;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE apod_db TO postgres;
