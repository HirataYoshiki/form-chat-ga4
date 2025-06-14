import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api';

// Assuming TenantCreatePayload structure from backend/models/tenant_models.py
// It's good practice to define these interfaces in a shared types file.
interface TenantCreatePayload {
  company_name: string;
  domain?: string | null; // Optional based on typical payload
  // Add other fields if defined in TenantCreatePayload and required/desired
}

const TenantCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [companyName, setCompanyName] = useState('');
  const [domain, setDomain] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    if (!companyName.trim()) {
      setError('Company name is required.');
      setLoading(false);
      return;
    }

    const payload: TenantCreatePayload = {
      company_name: companyName,
      domain: domain.trim() || null, // Send null if domain is empty
    };

    try {
      // Assuming this API requires superuser role and a valid token.
      // This call might fail if auth is not correctly set up or user is not superuser.
      await apiClient.post('/tenants', payload);
      // On successful creation, navigate back to the tenant list page
      navigate('/admin/tenants');
    } catch (err: any) {
      console.error('Error creating tenant:', err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(`Failed to create tenant: ${err.response.data.detail}`);
      } else {
        setError('Failed to create tenant. Please check console for details.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Basic inline styles, similar to other components
  const styles = {
    container: { padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '600px', margin: 'auto' },
    heading: { color: '#333', marginBottom: '20px', textAlign: 'center' as 'center' },
    form: {},
    formGroup: { marginBottom: '15px' },
    label: { display: 'block', marginBottom: '5px', color: '#555', fontSize: '14px' },
    input: {
      width: 'calc(100% - 22px)', // Account for padding and border
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
    error: { color: 'red', marginBottom: '15px', textAlign: 'center' as 'center'},
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

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>Create New Tenant</h1>
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
            <button type="button" style={styles.cancelButton} onClick={() => navigate('/admin/tenants')} disabled={loading}>
                Cancel
            </button>
            <button type="submit" style={styles.button} disabled={loading}>
                {loading ? 'Creating...' : 'Create Tenant'}
            </button>
        </div>
      </form>
    </div>
  );
};

export default TenantCreatePage;
