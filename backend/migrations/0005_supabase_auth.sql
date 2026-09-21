-- Identity moves to Supabase Auth. `users` becomes a local profile row keyed by the
-- Supabase auth user id (created on first authenticated request), so wardrobe/inspiration
-- foreign keys keep working.
--
-- Non-destructive for existing data: legacy accounts stay in place (orphaned -- they can
-- no longer log in). Email is no longer unique locally because Supabase enforces that,
-- and a legacy test account may share an email with a new Supabase account.

DROP TABLE refresh_tokens;

ALTER TABLE users DROP COLUMN password_hash;
ALTER TABLE users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE users DROP CONSTRAINT users_email_key;
CREATE INDEX idx_users_email ON users (email);
