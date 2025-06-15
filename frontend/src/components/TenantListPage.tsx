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
  const [hoveredRowId, setHoveredRowId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalCount, setTotalCount] = useState<number>(0);

  const ITEMS_PER_PAGE = 20;

  const fetchTenants = useCallback(async () => {
    setLoading(true);
    setError(null);
    const skip = (currentPage - 1) * ITEMS_PER_PAGE;
    const limit = ITEMS_PER_PAGE;

    try {
      const response = await apiClient.get<TenantListResponse>('/tenants', {
        params: { skip, limit, show_deleted: false },
      });
      setTenants(response.data.tenants);
      setTotalCount(response.data.total_count);
    } catch (err: any) {
      setError('Failed to fetch tenants. Ensure you are logged in with superuser privileges and the backend is running.');
      console.error('Error fetching tenants:', err);
    } finally {
      setLoading(false);
    }
  }, [currentPage]);

  useEffect(() => {
    fetchTenants();
  }, [fetchTenants]);

  const handleDelete = async (tenantId: string, tenantName: string) => {
    if (window.confirm(`Are you sure you want to delete tenant: ${tenantName} (ID: ${tenantId})?`)) {
      setDeletingTenantId(tenantId);
      try {
        await apiClient.delete(`/tenants/${tenantId}`);
        // If on the last page and deleting the last item, adjust currentPage
        if (tenants.length === 1 && currentPage > 1) {
            setCurrentPage(prev => prev - 1);
        } else {
            fetchTenants();
        }
      } catch (err: any) {
        console.error('Error deleting tenant:', err);
        const errorMsg = err.response?.data?.detail || 'An unknown error occurred.';
        setError(`Failed to delete tenant ${tenantName}. ${errorMsg}`);
      } finally {
        setDeletingTenantId(null);
      }
    }
  };

  const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

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
      marginRight: '8px',
      marginBottom: '5px',
      padding: '5px 10px',
      border: '1px solid #ccc',
      borderRadius: '4px',
      cursor: 'pointer',
    },
    errorText: { color: 'red', marginTop: '10px', marginBottom: '10px'},
    trHover: { backgroundColor: '#f5f5f5' },
    loadingText: { fontSize: '18px', color: '#555', textAlign: 'center' as 'center', padding: '20px' },
    paginationControls: {
      marginTop: '20px',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center'
    },
    paginationButton: {
      padding: '8px 12px',
      margin: '0 5px',
      border: '1px solid #ccc',
      borderRadius: '4px',
      cursor: 'pointer',
      backgroundColor: '#f0f0f0'
    },
    paginationInfo: {
      margin: '0 10px',
      fontSize: '0.9em'
    },
  };

  if (loading && tenants.length === 0 && currentPage === 1) { // Show initial loading only on first page load
    return <p style={styles.loadingText}>Loading tenants...</p>;
  }

  if (error && tenants.length === 0 && !deletingTenantId) {
    return <p style={styles.errorText}>{error}</p>;
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

      {!loading && tenants.length === 0 && !error && ( // Ensure not loading and no error before showing "no tenants"
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
                    <button style={styles.button} disabled={!!deletingTenantId}>Edit</button>
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
                      disabled={!!deletingTenantId}
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

      {totalPages > 1 && (
        <div style={styles.paginationControls}>
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1 || loading || !!deletingTenantId}
            style={styles.paginationButton}
          >
            Previous
          </button>
          <span style={styles.paginationInfo}>
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages || totalPages === 0 || loading || !!deletingTenantId}
            style={styles.paginationButton}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default TenantListPage;
