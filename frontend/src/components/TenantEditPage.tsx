import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api';

// Assuming TenantUpdatePayload and TenantResponse structures
// These should ideally be in a shared types/models file.
interface TenantData { // Represents the data structure for a tenant
  id: string;
  company_name: string;
  domain: string | null;
  // Add other fields from TenantResponse that you want to display/edit
}

interface TenantUpdatePayload {
  company_name?: string;
  domain?: string | null;
  // Add other updatable fields
}

const TenantEditPage: React.FC = () => {
  const { tenantId } = useParams<{ tenantId: string }>();
  const navigate = useNavigate();

  const [companyName, setCompanyName] = useState('');
  const [domain, setDomain] = useState('');
  const [originalTenant, setOriginalTenant] = useState<TenantData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [pageLoading, setPageLoading] = useState<boolean>(true);


  useEffect(() => {
    const fetchTenant = async () => {
      if (!tenantId) {
        setError('Tenant ID is missing from URL.');
        setPageLoading(false);
        return;
      }
      setPageLoading(true);
      try {
        const response = await apiClient.get<TenantData>(`/tenants/${tenantId}`);
        setOriginalTenant(response.data);
        setCompanyName(response.data.company_name);
        setDomain(response.data.domain || '');
      } catch (err: any) {
        console.error('Error fetching tenant:', err);
        setError('Failed to fetch tenant details.');
      } finally {
        setPageLoading(false);
      }
    };
    fetchTenant();
  }, [tenantId]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    if (!companyName.trim()) {
      setError('Company name is required.');
      setLoading(false);
      return;
    }

    const payload: TenantUpdatePayload = {
      company_name: companyName,
      domain: domain.trim() || null,
    };

    try {
      await apiClient.put(`/tenants/${tenantId}`, payload);
      navigate('/admin/tenants');
    } catch (err: any) {
      console.error('Error updating tenant:', err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(`Failed to update tenant: ${err.response.data.detail}`);
      } else {
        setError('Failed to update tenant. Please check console for details.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Basic inline styles
  const styles = {
    container: { padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '600px', margin: 'auto' },
    heading: { color: '#333', marginBottom: '20px', textAlign: 'center' as 'center' },
    form: {},
    formGroup: { marginBottom: '15px' },
    label: { display: 'block', marginBottom: '5px', color: '#555', fontSize: '14px' },
    input: {
      width: 'calc(100% - 22px)',
      padding: '10px',
      border: '1px solid #ddd',
      borderRadius: '4px',
      fontSize: '16px',
    },
    button: {
      padding: '10px 15px',
      backgroundColor: '#007bff',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      fontSize: '16px',
      cursor: 'pointer',
      opacity: loading ? 0.7 : 1,
    },
    error: { color: 'red', marginBottom: '15px', textAlign: 'center' as 'center' },
    actions: { marginTop: '20px', textAlign: 'right' as 'right' },
    cancelButton: {
        padding: '10px 15px',
        backgroundColor: '#6c757d',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        fontSize: '16px',
        cursor: 'pointer',
        marginRight: '10px',
    }
  };

  if (pageLoading) {
    return <p>Loading tenant details...</p>;
  }

  if (!originalTenant && !error) { // If no tenant data and no explicit error yet after loading
    return <p>Tenant not found or could not be loaded.</p>;
  }

  // Display error prominently if one occurred during fetch or submit
  if (error && !loading) { // Show general page error if not in submission loading state
      // If originalTenant exists, we can still show the form with an error message
      // Otherwise, a more general error message might be needed or redirect
      if (!originalTenant) return <p style={styles.error}>Error: {error}. <button onClick={() => navigate('/admin/tenants')}>Back to List</button></p>;
  }


  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>Edit Tenant (ID: {tenantId})</h1>
      {error && <p style={styles.error}>{error}</p>}
      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.formGroup}>
          <label htmlFor="companyName" style={styles.label}>Company Name <span style={{color: 'red'}}>*</span></label>
          <input
            type="text"
            id="companyName"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            required
            style={styles.input}
            disabled={loading}
          />
        </div>
        <div style={styles.formGroup}>
          <label htmlFor="domain" style={styles.label}>Domain</label>
          <input
            type="text"
            id="domain"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            style={styles.input}
            disabled={loading}
          />
        </div>
        <div style={styles.actions}>
           <button type="button" style={styles.cancelButton} onClick={() => navigate('/admin/tenants')} disabled={loading || pageLoading}>
                Cancel
            </button>
            <button type="submit" style={styles.button} disabled={loading || pageLoading}>
                {loading ? 'Updating...' : 'Update Tenant'}
            </button>
        </div>
      </form>
    </div>
  );
};

export default TenantEditPage;
