import React from 'react';
import { Navigate, useLocation, Outlet, useNavigate } from 'react-router-dom'; // Added useNavigate
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute: React.FC = () => {
  const { userProfile, appRole, authLoading } = useAuth(); // Use userProfile and appRole
  const location = useLocation();
  const navigate = useNavigate(); // For programmatic navigation

  // Basic inline styles
  const styles = {
    loadingContainer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      fontFamily: 'Arial, sans-serif',
      fontSize: '18px',
    },
    unauthorizedContainer: { // Simple style for unauthorized message page
      padding: '20px',
      fontFamily: 'Arial, sans-serif',
      textAlign: 'center' as 'center',
      marginTop: '50px'
    },
    button: { // Basic button style for unauthorized page
      padding: '10px 15px',
      backgroundColor: '#007bff',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      fontSize: '16px',
      cursor: 'pointer',
      marginTop: '20px',
    }
  };

  if (authLoading) {
    return <div style={styles.loadingContainer}>Checking authentication...</div>;
  }

  if (!userProfile) {
    // User not authenticated (or profile failed to load), redirect to login page
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (appRole !== 'superuser') {
    // User is authenticated but not a superuser.
    // Render an "Access Denied" message directly.
    return (
      <div style={styles.unauthorizedContainer}>
        <h1>Access Denied</h1>
        <p>You do not have the necessary permissions to view this page.</p>
        <button style={styles.button} onClick={() => navigate('/')}>Go to Homepage</button>
      </div>
    );
  }

  // User is authenticated and is a superuser
  return <Outlet />;
};

export default ProtectedRoute;
