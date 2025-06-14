import React, { useState, ChangeEvent } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiClient from '../api';

// Based on backend/models/rag_models.py (RagFileUploadResponse and RagUploadedFileDetail)
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

// Define allowed extensions
const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx', '.pptx', '.xlsx'];

const RagFileManagementPage: React.FC = () => {
  const { tenantId } = useParams<{ tenantId: string }>();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResponse, setUploadResponse] = useState<RagFileUploadResponse | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setUploadResponse(null); // Clear previous upload response

    if (event.target.files) {
      const newFiles = Array.from(event.target.files);
      const validFiles: File[] = [];
      const invalidFileNames: string[] = [];

      for (const file of newFiles) {
        const fileName = file.name;
        // Use lastIndexOf('.') to find the last dot, then substring to get the extension.
        // Handle cases where filename might not have a dot or starts with a dot.
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
        setSelectedFiles(validFiles); // Keep only valid files
      } else {
        setSelectedFiles(newFiles); // All files are valid
      }
      // Clear the input value to allow selecting the same file(s) again if an error occurred or after removal
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

  const styles = {
    container: { padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: 'auto' },
    heading: { color: '#333', marginBottom: '10px' },
    subHeading: { color: '#555', marginBottom: '20px', fontSize: '0.9em'},
    breadcrumb: { marginBottom: '20px' },
    formGroup: { marginBottom: '20px' },
    label: { display: 'block', marginBottom: '8px', fontWeight: 'bold' },
    inputFile: {
      padding: '10px',
      border: '1px solid #ccc',
      borderRadius: '4px',
      width: 'calc(100% - 22px)',
    },
    fileList: { listStyle: 'none', padding: 0, marginBottom: '20px' },
    fileListItem: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '8px',
      borderBottom: '1px solid #eee',
      fontSize: '0.9em',
    },
    removeButton: {
      padding: '3px 8px',
      backgroundColor: '#ff4d4f',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      cursor: 'pointer',
      fontSize: '0.8em',
    },
    uploadButton: {
      padding: '10px 20px',
      backgroundColor: '#007bff',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      fontSize: '16px',
      cursor: 'pointer',
      opacity: uploading ? 0.7 : 1,
    },
    error: { color: 'red', marginBottom: '15px', whiteSpace: 'pre-wrap' as 'pre-wrap' }, // Added pre-wrap for multi-line errors
    resultArea: { marginTop: '20px', padding: '15px', border: '1px solid #eee', borderRadius: '4px', backgroundColor: '#f9f9f9'},
    resultList: { listStyleType: 'disc', paddingLeft: '20px' },
    resultListItem: { marginBottom: '5px' },
  };

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
        <input
          type="file"
          id="file-upload"
          multiple
          onChange={handleFileChange}
          style={styles.inputFile}
          disabled={uploading}
          accept={ALLOWED_EXTENSIONS.join(',')} // Add accept attribute for better UX
        />
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

      <button
        onClick={handleUpload}
        style={styles.uploadButton}
        disabled={selectedFiles.length === 0 || uploading}
      >
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
    </div>
  );
};

export default RagFileManagementPage;
