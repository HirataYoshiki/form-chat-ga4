-- Migration: Add RAG related columns to tenants and create rag_uploaded_files table

-- 1. Alter the `tenants` table
ALTER TABLE public.tenants
ADD COLUMN IF NOT EXISTS rag_corpus_id TEXT,
ADD COLUMN IF NOT EXISTS rag_corpus_display_name TEXT;

COMMENT ON COLUMN public.tenants.rag_corpus_id IS 'Vertex AI RAG Corpus ID associated with this tenant.';
COMMENT ON COLUMN public.tenants.rag_corpus_display_name IS 'Display name for the RAG Corpus associated with this tenant.';


-- 2. Create the new `rag_uploaded_files` table
CREATE TABLE IF NOT EXISTS public.rag_uploaded_files (
    processing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(tenant_id) ON DELETE CASCADE,
    uploaded_by_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE, -- Assuming public.users is the profiles table linked to auth.users
    original_filename TEXT NOT NULL,
    gcs_upload_path TEXT NOT NULL,
    gcs_processed_path TEXT,
    file_size BIGINT NOT NULL,
    file_type TEXT NOT NULL, -- e.g., 'pdf', 'docx', 'csv', 'txt'
    upload_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processing_status TEXT NOT NULL DEFAULT 'pending', -- e.g., 'pending', 'preprocessing', 'importing', 'completed', 'failed'
    status_message TEXT,
    vertex_ai_rag_file_id TEXT, -- Stores the RagFile.name from Vertex AI
    vertex_ai_operation_name TEXT, -- Stores the LRO name from import_rag_files
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.rag_uploaded_files IS 'Tracks files uploaded by tenants for RAG processing.';
COMMENT ON COLUMN public.rag_uploaded_files.processing_id IS 'Unique ID for this processing job/file upload instance.';
COMMENT ON COLUMN public.rag_uploaded_files.tenant_id IS 'Tenant associated with this uploaded file.';
COMMENT ON COLUMN public.rag_uploaded_files.uploaded_by_user_id IS 'User who uploaded the file.';
COMMENT ON COLUMN public.rag_uploaded_files.original_filename IS 'Original name of the uploaded file.';
COMMENT ON COLUMN public.rag_uploaded_files.gcs_upload_path IS 'GCS path where the original uploaded file is stored.';
COMMENT ON COLUMN public.rag_uploaded_files.gcs_processed_path IS 'GCS path where the processed (e.g., chunked) file is stored, if applicable.';
COMMENT ON COLUMN public.rag_uploaded_files.file_size IS 'Size of the original file in bytes.';
COMMENT ON COLUMN public.rag_uploaded_files.file_type IS 'Detected or provided file type (e.g., pdf, docx).';
COMMENT ON COLUMN public.rag_uploaded_files.upload_timestamp IS 'Timestamp when the file was originally uploaded by the user.';
COMMENT ON COLUMN public.rag_uploaded_files.processing_status IS 'Current status of the file in the RAG pipeline.';
COMMENT ON COLUMN public.rag_uploaded_files.status_message IS 'Detailed message about the current processing_status, especially for errors.';
COMMENT ON COLUMN public.rag_uploaded_files.vertex_ai_rag_file_id IS 'The RagFile.name resource ID from Vertex AI after successful import.';
COMMENT ON COLUMN public.rag_uploaded_files.vertex_ai_operation_name IS 'The Long-Running Operation (LRO) name from Vertex AI for an import_rag_files call.';


-- Grant permissions for the new table to authenticated users and service_role
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.rag_uploaded_files TO authenticated;
GRANT ALL ON TABLE public.rag_uploaded_files TO service_role;

-- Optional: Add RLS policies if needed, similar to other tables.
-- For now, keeping it simple. Policies might be needed to restrict access per tenant.
-- Example (adjust as needed):
-- ALTER TABLE public.rag_uploaded_files ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Tenant can manage their own rag_uploaded_files"
-- ON public.rag_uploaded_files
-- FOR ALL
-- TO authenticated
-- USING (tenant_id = (SELECT tenant_id FROM public.users WHERE id = auth.uid()))
-- WITH CHECK (tenant_id = (SELECT tenant_id FROM public.users WHERE id = auth.uid()));
-- CREATE POLICY "Superusers can access all rag_uploaded_files"
-- ON public.rag_uploaded_files
-- FOR ALL
-- TO authenticated
-- USING ((SELECT app_role FROM public.users WHERE id = auth.uid()) = 'superuser');


-- Trigger to automatically update updated_at timestamp
CREATE OR REPLACE TRIGGER handle_updated_at_rag_uploaded_files
BEFORE UPDATE ON public.rag_uploaded_files
FOR EACH ROW
EXECUTE FUNCTION extensions.moddatetime('updated_at');
