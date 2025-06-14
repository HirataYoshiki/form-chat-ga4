import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api';

interface Tenant {
  id: string;
  company_name: string;
  domain: string | null;
  created_at: string;
}

interface TenantListResponse {
  tenants: Tenant[];
  total_count: number;
  skip: number;
  limit: number;
}

const TenantListPage: React.FC = () => {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingTenantId, setDeletingTenantId] = useState<string | null>(null);
  const [hoveredRowId, setHoveredRowId] = useState<string | null>(null); // For row hover effect

  const fetchTenants = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<TenantListResponse>('/tenants');
      setTenants(response.data.tenants);
    } catch (err: any) {
      setError('Failed to fetch tenants. Ensure you are logged in with superuser privileges and the backend is running.');
      console.error('Error fetching tenants:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTenants();
  }, [fetchTenants]);

  const handleDelete = async (tenantId: string, tenantName: string) => {
    if (window.confirm(`Are you sure you want to delete tenant: ${tenantName} (ID: ${tenantId})?`)) {
      setDeletingTenantId(tenantId);
      try {
        await apiClient.delete(`/tenants/${tenantId}`);
        fetchTenants();
      } catch (err: any) {
        console.error('Error deleting tenant:', err);
        const errorMsg = err.response?.data?.detail || 'An unknown error occurred.';
        setError(`Failed to delete tenant ${tenantName}. ${errorMsg}`);
      } finally {
        setDeletingTenantId(null);
      }
    }
  };

  const styles = {
    container: { padding: '20px', fontFamily: 'Arial, sans-serif' },
    heading: { color: '#333', marginBottom: '20px' },
    table: { width: '100%', borderCollapse: 'collapse' as 'collapse' },
    th: {
      borderBottom: '2px solid #ddd',
      padding: '10px',
      textAlign: 'left' as 'left',
      backgroundColor: '#f0f0f0',
    },
    td: {
      borderBottom: '1px solid #eee',
      padding: '10px',
    },
    button: {
      marginRight: '8px', // Adjusted spacing
      marginBottom: '5px', // Added for potential wrapping
      padding: '5px 10px',
      border: '1px solid #ccc',
      borderRadius: '4px',
      cursor: 'pointer',
    },
    errorText: { color: 'red', marginTop: '10px', marginBottom: '10px'},
    trHover: { backgroundColor: '#f5f5f5' }, // Style for hovered row
    loadingText: { fontSize: '18px', color: '#555', textAlign: 'center' as 'center', padding: '20px' }, // Style for loading text
  };

  if (loading && tenants.length === 0) {
    return <p style={styles.loadingText}>Loading tenants...</p>;
  }

  if (error && tenants.length === 0 && !deletingTenantId) {
    return <p style={styles.errorText}>{error}</p>; // Use errorText style
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>Tenant Management</h1>
      <div style={{ marginBottom: '20px' }}>
        <Link to="/admin/tenants/new">
          <button style={styles.button}>Create New Tenant</button>
        </Link>
      </div>

      {error && <p style={styles.errorText}>{error}</p>}

      {loading && <p style={styles.loadingText}>Refreshing tenant list...</p>}

      {tenants.length === 0 && !loading && !error && (
        <p>No tenants found.</p>
      )}

      {tenants.length > 0 && (
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>ID</th>
              <th style={styles.th}>Company Name</th>
              <th style={styles.th}>Domain</th>
              <th style={styles.th}>Created At</th>
              <th style={styles.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((tenant) => (
              <tr
                key={tenant.id}
                style={tenant.id === hoveredRowId ? styles.trHover : undefined}
                onMouseEnter={() => setHoveredRowId(tenant.id)}
                onMouseLeave={() => setHoveredRowId(null)}
              >
                <td style={styles.td}>{tenant.id}</td>
                <td style={styles.td}>{tenant.company_name}</td>
                <td style={styles.td}>{tenant.domain || 'N/A'}</td>
                <td style={styles.td}>{new Date(tenant.created_at).toLocaleDateString()}</td>
                <td style={styles.td}>
                  <Link to={`/admin/tenants/edit/${tenant.id}`}>
                    <button style={styles.button} disabled={deletingTenantId === tenant.id}>Edit</button>
                  </Link>
                  <button
                    style={styles.button}
                    onClick={() => handleDelete(tenant.id, tenant.company_name)}
                    disabled={deletingTenantId === tenant.id}
                  >
                    {deletingTenantId === tenant.id ? 'Deleting...' : 'Delete'}
                  </button>
                  <Link to={`/admin/tenants/${tenant.id}/rag-files`}>
                    <button
                      style={styles.button}
                      disabled={deletingTenantId === tenant.id}
                    >
                      RAG Files
                    </button>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default TenantListPage;
