-- PostgreSQL schema for contact_submissions table, suitable for Supabase

-- Ensure the table is not created if it already exists
CREATE TABLE IF NOT EXISTS contact_submissions (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    ga_client_id TEXT,
    ga_session_id TEXT,
    form_id TEXT -- To associate with the data-form-id from the widget
);

-- Add comments to columns for better understanding
COMMENT ON COLUMN contact_submissions.id IS 'Auto-incrementing unique identifier for each submission';
COMMENT ON COLUMN contact_submissions.created_at IS 'Timestamp of when the submission was created';
COMMENT ON COLUMN contact_submissions.name IS 'Name of the person submitting the form';
COMMENT ON COLUMN contact_submissions.email IS 'Email address of the person submitting the form';
COMMENT ON COLUMN contact_submissions.message IS 'The message content from the form submission';
COMMENT ON COLUMN contact_submissions.ga_client_id IS 'Google Analytics Client ID, if available';
COMMENT ON COLUMN contact_submissions.ga_session_id IS 'Google Analytics Session ID, if available';
COMMENT ON COLUMN contact_submissions.form_id IS 'Identifier for the specific form used for this submission (e.g., from data-form-id attribute)';

-- Example of how to enable Row Level Security (RLS) - common in Supabase
-- This is typically done in the Supabase UI, but can be scripted.
-- Ensure RLS is enabled on the table.
-- ALTER TABLE contact_submissions ENABLE ROW LEVEL SECURITY;

-- Example: Allow public read-only access (adjust as needed for your security model)
-- This policy is very permissive and likely not suitable for production without modification.
-- CREATE POLICY "Allow public read access"
-- ON contact_submissions
-- FOR SELECT
-- USING (true);

-- Example: Allow authenticated users to insert their own data
-- (This assumes you have a way to link auth.uid() to submissions, which is not part of this basic schema yet)
-- CREATE POLICY "Allow authenticated users to insert"
-- ON contact_submissions
-- FOR INSERT
-- WITH CHECK (auth.role() = 'authenticated');

-- Note: Policies for UPDATE and DELETE would also be needed for full CRUD by users.
-- Supabase typically handles data insertion via its API using the service_role key,
-- which bypasses RLS by default, or via specific user roles if RLS is configured for inserts.
-- For this project, the FastAPI backend will likely use a service role key to insert data,
-- so insert policies for individual users might not be immediately necessary for the backend.
