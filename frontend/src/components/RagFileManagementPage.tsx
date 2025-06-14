import React, { useState, ChangeEvent, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiClient from '../api';

export enum RagProcessingStatus {
  PENDING_UPLOAD = "pending_upload",
  UPLOAD_TO_GCS_FAILED = "upload_to_gcs_failed",
  PENDING_PREPROCESS = "pending_preprocess",
  PREPROCESSING = "preprocessing",
  PREPROCESS_FAILED = "preprocess_failed",
  PENDING_INDEXING = "pending_indexing",
  INDEXING = "indexing",
  COMPLETED = "completed",
  FAILED = "failed",
  DELETING = "deleting",
  DELETED = "deleted",
}

export interface RagFileMetadata {
  processing_id: string;
  tenant_id: string;
  uploaded_by_user_id: string;
  original_filename: string;
  gcs_upload_path: string | null;
  gcs_processed_path?: string | null;
  file_size: number;
  file_type: string;
  upload_timestamp: string;
  processing_status: RagProcessingStatus;
  status_message?: string | null;
  vertex_ai_rag_file_id?: string | null;
  vertex_ai_operation_name?: string | null;
  last_processed_timestamp?: string | null;
}

export interface RagUploadedFileDetail {
  processing_id: string;
  original_filename: string;
  status_url: string;
  message?: string;
}

export interface RagFileUploadResponse {
  message: string;
  tenant_id: string;
  uploaded_files: RagUploadedFileDetail[];
}

const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx', '.pptx', '.xlsx'];

const RagFileManagementPage: React.FC = () => {
  const { tenantId } = useParams<{ tenantId: string }>();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResponse, setUploadResponse] = useState<RagFileUploadResponse | null>(null);

  const [uploadedFilesList, setUploadedFilesList] = useState<RagFileMetadata[]>([]);
  const [listLoading, setListLoading] = useState<boolean>(false);
  const [listError, setListError] = useState<string | null>(null);
  const [deletingFileId, setDeletingFileId] = useState<string | null>(null);
  const [updatingStatusForId, setUpdatingStatusForId] = useState<string | null>(null); // Step 1: Add state

  const fetchUploadedFiles = useCallback(async () => {
    if (!tenantId) return;
    setListLoading(true);
    setListError(null);
    try {
      const response = await apiClient.get<RagFileMetadata[]>(`/tenants/${tenantId}/rag_files`);
      setUploadedFilesList(response.data);
    } catch (err: any) {
      console.error('Error fetching uploaded files:', err);
      setListError('Failed to fetch uploaded files. ' + (err.response?.data?.detail || err.message || ''));
    } finally {
      setListLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    fetchUploadedFiles();
  }, [fetchUploadedFiles]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setUploadResponse(null);

    if (event.target.files) {
      const newFiles = Array.from(event.target.files);
      const validFiles: File[] = [];
      const invalidFileNames: string[] = [];

      for (const file of newFiles) {
        const fileName = file.name;
        const lastDotIndex = fileName.lastIndexOf('.');
        const fileExtension = lastDotIndex > 0 ? fileName.substring(lastDotIndex).toLowerCase() : "";

        if (ALLOWED_EXTENSIONS.includes(fileExtension)) {
          validFiles.push(file);
        } else {
          invalidFileNames.push(fileName);
        }
      }

      if (invalidFileNames.length > 0) {
        setError(
          `Invalid file type(s): ${invalidFileNames.join(', ')}. ` +
          `Allowed types: ${ALLOWED_EXTENSIONS.join(', ')}`
        );
        setSelectedFiles(validFiles);
      } else {
        setSelectedFiles(newFiles);
      }
      event.target.value = '';
    }
  };

  const handleRemoveFile = (fileName: string) => {
    setSelectedFiles(prevFiles => prevFiles.filter(file => file.name !== fileName));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError("Please select files to upload.");
      return;
    }
    setError(null);
    setUploadResponse(null);
    setUploading(true);

    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await apiClient.post<RagFileUploadResponse>(`/tenants/${tenantId}/rag_files`, formData);
      setUploadResponse(response.data);
      setSelectedFiles([]);
      fetchUploadedFiles();
    } catch (err: any) {
      console.error('Error uploading files:', err);
      if (err.response && err.response.data && err.response.data.detail) {
        if (Array.isArray(err.response.data.detail)) {
            setError(`Upload failed: ${err.response.data.detail.map((e: any) => e.msg).join(', ')}`);
        } else {
            setError(`Upload failed: ${err.response.data.detail}`);
        }
      } else if (err.message) {
        setError(`Upload failed: ${err.message}`);
      } else {
        setError('Upload failed. An unknown error occurred.');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteFile = async (processingId: string, fileName: string) => {
    if (!tenantId) return;
    if (!window.confirm(`Are you sure you want to delete the file: "${fileName}" (ID: ${processingId})? This action cannot be undone.`)) {
      return;
    }
    setDeletingFileId(processingId);
    setListError(null);
    try {
      await apiClient.delete(`/tenants/${tenantId}/rag_files/${processingId}`);
      fetchUploadedFiles();
    } catch (err: any) {
      console.error('Error deleting file:', err);
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
          setListError(`Failed to delete file "${fileName}": ${detail}`);
      } else if (Array.isArray(detail)) {
          setListError(`Failed to delete file "${fileName}": ${detail.map((e: any) => e.msg || String(e)).join(', ')}`);
      } else {
          setListError(`Failed to delete file "${fileName}". An unknown error occurred or no specific detail provided.`);
      }
    } finally {
      setDeletingFileId(null);
    }
  };

  // Step 2: Create handleRefreshStatus function
  const handleRefreshStatus = async (processingIdToRefresh: string) => {
    if (!tenantId) return;
    setUpdatingStatusForId(processingIdToRefresh);
    setListError(null);

    try {
      const response = await apiClient.get<RagFileMetadata>(
        `/tenants/${tenantId}/rag_files/${processingIdToRefresh}/status`
      );
      setUploadedFilesList(prevList =>
        prevList.map(file =>
          file.processing_id === processingIdToRefresh
            ? { ...response.data } // Replace with new data from status endpoint
            : file
        )
      );
    } catch (err: any) {
      console.error(`Error refreshing status for ${processingIdToRefresh}:`, err);
      const detail = err.response?.data?.detail;
      let message = `Failed to refresh status for file ID ${processingIdToRefresh}.`;
      if (typeof detail === 'string') {
          message += ` ${detail}`;
      } else if (Array.isArray(detail)) {
          message += ` ${detail.map((e: any) => e.msg || String(e)).join(', ')}`;
      }
      setListError(message);
    } finally {
      setUpdatingStatusForId(null);
    }
  };

  const getStatusStyle = (status: RagProcessingStatus): React.CSSProperties => {
    switch (status) {
      case RagProcessingStatus.PENDING_UPLOAD:
      case RagProcessingStatus.PENDING_PREPROCESS:
      case RagProcessingStatus.PENDING_INDEXING:
        return { color: '#d39e00', fontWeight: 'bold' };
      case RagProcessingStatus.PREPROCESSING:
      case RagProcessingStatus.INDEXING:
        return { color: '#007bff', fontWeight: 'bold' };
      case RagProcessingStatus.COMPLETED:
        return { color: '#28a745', fontWeight: 'bold' };
      case RagProcessingStatus.UPLOAD_TO_GCS_FAILED:
      case RagProcessingStatus.PREPROCESS_FAILED:
      case RagProcessingStatus.FAILED:
        return { color: '#dc3545', fontWeight: 'bold' };
      case RagProcessingStatus.DELETING:
      case RagProcessingStatus.DELETED:
        return { color: '#6c757d', fontWeight: 'bold' };
      default:
        return { color: '#343a40' };
    }
  };

  const renderStatusDisplay = (status: RagProcessingStatus, message?: string | null): JSX.Element => {
    const statusText = status.replace(/_/g, ' ').toUpperCase();
    let displayMessage = statusText;
    let icon = '';
    switch (status) {
      case RagProcessingStatus.PENDING_UPLOAD: case RagProcessingStatus.PENDING_PREPROCESS: case RagProcessingStatus.PENDING_INDEXING: icon = '⏳ '; break;
      case RagProcessingStatus.PREPROCESSING: case RagProcessingStatus.INDEXING: icon = '🔄 '; break;
      case RagProcessingStatus.COMPLETED: icon = '✅ '; break;
      case RagProcessingStatus.UPLOAD_TO_GCS_FAILED: case RagProcessingStatus.PREPROCESS_FAILED: case RagProcessingStatus.FAILED: icon = '❌ '; break;
      case RagProcessingStatus.DELETING: case RagProcessingStatus.DELETED: icon = '🗑️ '; break;
      default: icon = 'ℹ️ ';
    }
    const titleMessage = message && message.trim() !== "" && message.toLowerCase() !== "completed" ? `${statusText}: ${message}` : statusText;
    return (<span style={getStatusStyle(status)} title={titleMessage}>{icon}{displayMessage}</span>);
  };

  const styles = {
    container: { padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '900px', margin: 'auto' },
    heading: { color: '#333', marginBottom: '10px' },
    subHeading: { color: '#555', marginBottom: '20px', fontSize: '0.9em'},
    breadcrumb: { marginBottom: '20px' },
    formGroup: { marginBottom: '20px' },
    label: { display: 'block', marginBottom: '8px', fontWeight: 'bold' },
    inputFile: { padding: '10px', border: '1px solid #ccc', borderRadius: '4px', width: 'calc(100% - 22px)'},
    fileList: { listStyle: 'none', padding: 0, marginBottom: '20px' },
    fileListItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px', borderBottom: '1px solid #eee', fontSize: '0.9em'},
    removeButton: { padding: '3px 8px', backgroundColor: '#ff4d4f', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8em'},
    uploadButton: { padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', fontSize: '16px', cursor: 'pointer', opacity: uploading ? 0.7 : 1},
    error: { color: 'red', marginBottom: '15px', whiteSpace: 'pre-wrap' as 'pre-wrap' },
    resultArea: { marginTop: '20px', padding: '15px', border: '1px solid #eee', borderRadius: '4px', backgroundColor: '#f9f9f9'},
    resultList: { listStyleType: 'disc', paddingLeft: '20px' },
    resultListItem: { marginBottom: '5px' },
    table: { width: '100%', borderCollapse: 'collapse' as 'collapse', marginTop: '20px' },
    th: { borderBottom: '2px solid #ddd', padding: '10px 12px', textAlign: 'left' as 'left', backgroundColor: '#f0f0f0', fontSize: '0.9em' },
    td: { borderBottom: '1px solid #eee', padding: '10px 12px', fontSize: '0.9em', verticalAlign: 'middle' },
    actionButtonSmall: { fontSize: '0.8em', padding: '3px 8px', marginRight: '5px', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer', backgroundColor: '#f0f0f0' },
    deleteButtonSmall: { fontSize: '0.8em', padding: '3px 8px', marginRight: '5px', border: '1px solid #ff4d4f', borderRadius: '4px', cursor: 'pointer', color: '#ff4d4f', backgroundColor: 'white'},
    refreshButtonSmall: { fontSize: '0.8em', padding: '3px 8px', marginRight: '5px', border: '1px solid #007bff', borderRadius: '4px', cursor: 'pointer', color: '#007bff', backgroundColor: 'white'},
  };

  // Merging deleteButtonSmall into actionButtonSmall might have been an error if they are distinct.
  // Let's define actionButtonSmall as a base and let delete/refresh inherit or be separate.
  // For now, the previous merge `styles.actionButtonSmall = { ...styles.actionButtonSmall, ...styles.deleteButtonSmall };`
  // makes actionButtonSmall look like a delete button. This needs to be handled carefully.
  // I will use specific styles for delete and refresh.

  return (
    <div style={styles.container}>
      <div style={styles.breadcrumb}>
        <Link to="/admin/tenants">Tenant List</Link> / Tenant ID: {tenantId} / RAG Files
      </div>
      <h1 style={styles.heading}>RAG File Management</h1>
      <p style={styles.subHeading}>Upload new files to be used for Retrieval Augmented Generation for this tenant. Allowed types: {ALLOWED_EXTENSIONS.join(', ')}</p>

      {error && <p style={styles.error}>{error}</p>}

      <div style={styles.formGroup}>
        <label htmlFor="file-upload" style={styles.label}>Select Files:</label>
        <input type="file" id="file-upload" multiple onChange={handleFileChange} style={styles.inputFile} disabled={uploading || listLoading} accept={ALLOWED_EXTENSIONS.join(',')}/>
        <p style={{fontSize: '0.8em', color: '#777', marginTop: '5px'}}>You can select multiple files.</p>
      </div>

      {selectedFiles.length > 0 && (
        <div>
          <h3 style={{fontSize: '1.1em', marginBottom: '10px'}}>Selected Files ({selectedFiles.length}):</h3>
          <ul style={styles.fileList}>
            {selectedFiles.map((file, index) => (
              <li key={index} style={styles.fileListItem}>
                <span>{file.name} ({(file.size / 1024).toFixed(2)} KB)</span>
                <button onClick={() => handleRemoveFile(file.name)} style={styles.removeButton} disabled={uploading}>Remove</button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <button onClick={handleUpload} style={styles.uploadButton} disabled={selectedFiles.length === 0 || uploading || listLoading}>
        {uploading ? 'Uploading...' : 'Upload Selected Files'}
      </button>

      {uploadResponse && (
        <div style={styles.resultArea}>
          <h4>Upload Results:</h4>
          <p>{uploadResponse.message}</p>
          {uploadResponse.uploaded_files && uploadResponse.uploaded_files.length > 0 && (
            <ul style={styles.resultList}>
              {uploadResponse.uploaded_files.map(f => (
                <li key={f.processing_id} style={styles.resultListItem}>
                  <strong>{f.original_filename}</strong>
                  {f.message && <span> - Message: {f.message}</span>}
                  <br />
                  Processing ID: {f.processing_id}
                  <br />
                  Status URL: <a href={f.status_url} target="_blank" rel="noopener noreferrer">{f.status_url}</a>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div style={{marginTop: '30px'}}>
        <h3>Uploaded Files</h3>
        {listLoading && <p>Loading file list...</p>}
        {listError && <p style={styles.error}>{listError}</p>}
        {!listLoading && !listError && uploadedFilesList.length === 0 && (
          <p>No files have been uploaded for this tenant yet.</p>
        )}
        {!listLoading && !listError && uploadedFilesList.length > 0 && (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Filename</th>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Size (KB)</th>
                <th style={styles.th}>Uploaded</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {uploadedFilesList.map((file) => (
                <tr key={file.processing_id}>
                  <td style={styles.td} title={file.original_filename}>
                    {file.original_filename.length > 30 ? `${file.original_filename.substring(0,27)}...` : file.original_filename}
                  </td>
                  <td style={styles.td}>{file.file_type}</td>
                  <td style={styles.td}>{(file.file_size / 1024).toFixed(2)}</td>
                  <td style={styles.td}>{new Date(file.upload_timestamp).toLocaleString()}</td>
                  <td style={styles.td}>
                    {renderStatusDisplay(file.processing_status, file.status_message)}
                  </td>
                  <td style={styles.td}>
                    <button
                      style={styles.refreshButtonSmall} // Use refresh style
                      onClick={() => handleRefreshStatus(file.processing_id)}
                      disabled={
                        deletingFileId === file.processing_id ||
                        updatingStatusForId === file.processing_id ||
                        listLoading ||
                        uploading
                      }
                    >
                      {updatingStatusForId === file.processing_id ? 'Refreshing...' : 'Refresh'}
                    </button>
                    <button
                      style={styles.deleteButtonSmall} // Use specific delete style
                      onClick={() => handleDeleteFile(file.processing_id, file.original_filename)}
                      disabled={
                        deletingFileId === file.processing_id ||
                        updatingStatusForId === file.processing_id || // Also disable if other action on this row is pending
                        listLoading ||
                        uploading
                      }
                    >
                      {deletingFileId === file.processing_id ? 'Deleting...' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default RagFileManagementPage;
