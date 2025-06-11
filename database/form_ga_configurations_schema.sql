-- Schema for form_ga_configurations table
-- This table stores Google Analytics 4 Measurement Protocol configurations per form_id.

CREATE TABLE IF NOT EXISTS form_ga_configurations (
    form_id TEXT PRIMARY KEY,
    ga4_measurement_id TEXT NOT NULL,
    ga4_api_secret TEXT NOT NULL, -- IMPORTANT: Store encrypted in a real production system
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE form_ga_configurations IS 'Stores GA4 Measurement Protocol configurations for each form.';
COMMENT ON COLUMN form_ga_configurations.form_id IS 'Unique identifier for the form (e.g., from data-form-id attribute).';
COMMENT ON COLUMN form_ga_configurations.ga4_measurement_id IS 'GA4 Measurement ID (e.g., G-XXXXXXXXXX).';
COMMENT ON COLUMN form_ga_configurations.ga4_api_secret IS 'GA4 API Secret for Measurement Protocol. IMPORTANT: This should be encrypted at rest in production.';
COMMENT ON COLUMN form_ga_configurations.description IS 'Optional description for this configuration set.';
COMMENT ON COLUMN form_ga_configurations.created_at IS 'Timestamp of when this configuration was created.';
COMMENT ON COLUMN form_ga_configurations.updated_at IS 'Timestamp of when this configuration was last updated.';

-- Trigger to automatically update updated_at timestamp on row update
-- This is PostgreSQL specific.
CREATE OR REPLACE FUNCTION update_updated_at_column_form_ga_config() -- Renamed function to be more specific
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Ensure the trigger name is unique if similar triggers exist for other tables.
CREATE TRIGGER trigger_update_form_ga_configurations_updated_at
BEFORE UPDATE ON form_ga_configurations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column_form_ga_config(); -- Use renamed function
