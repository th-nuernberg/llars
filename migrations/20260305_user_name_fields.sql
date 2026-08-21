-- Add first_name, last_name, display_name to users table
-- These fields enable searching users by real name (e.g., "Philipp" finds "ieb-steigerwald")

ALTER TABLE users ADD COLUMN first_name VARCHAR(100) DEFAULT NULL AFTER collab_color;
ALTER TABLE users ADD COLUMN last_name VARCHAR(100) DEFAULT NULL AFTER first_name;
ALTER TABLE users ADD COLUMN display_name VARCHAR(255) DEFAULT NULL AFTER last_name;

-- Add index for name-based search
CREATE INDEX idx_users_display_name ON users (display_name);
CREATE INDEX idx_users_first_name ON users (first_name);
CREATE INDEX idx_users_last_name ON users (last_name);
