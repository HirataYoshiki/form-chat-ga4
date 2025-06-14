import React from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom';
import TenantListPage from './components/TenantListPage';
import TenantCreatePage from './components/TenantCreatePage';
import TenantEditPage from './components/TenantEditPage';
import LoginPage from './components/LoginPage';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider, useAuth } from './contexts/AuthContext'; // Import useAuth

// Placeholder for a HomePage component
const HomePage: React.FC = () => (
  <div>
    <h1>Home Page</h1>
    <nav>
      <ul>
        <li>
          <Link to="/admin/tenants">Tenant Management</Link>
        </li>
        {/* Add other links as needed */}
      </ul>
    </nav>
  </div>
);

// Placeholder for a NotFoundPage component
const NotFoundPage: React.FC = () => (
  <div>
    <h1>404 - Page Not Found</h1>
    <p>The page you are looking for does not exist.</p>
    <Link to="/">Go to Home</Link>
  </div>
);

// Main App component content (inside AuthProvider)
const AppContent: React.FC = () => {
  const { supabaseUser, userProfile, appRole, logout } = useAuth(); // Updated destructuring
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login'); // Redirect to login page after logout
    } catch (error) {
      console.error("Failed to logout:", error);
      // Optionally, show an error message to the user
    }
  };

  // Basic inline styles for the app layout (can be moved outside if preferred)
  const styles = {
    nav: {
      backgroundColor: '#f0f0f0',
      padding: '10px',
      marginBottom: '20px',
      borderBottom: '1px solid #ddd',
    },
    ul: {
      listStyleType: 'none' as 'none',
      padding: 0,
      margin: 0,
      display: 'flex',
      alignItems: 'center', // Vertically align items in nav
    },
    li: {
      marginRight: '15px',
    },
    link: {
      textDecoration: 'none',
      color: '#007bff',
      fontWeight: 'bold',
    },
    logoutButton: { // Specific style for logout button to mimic link
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      padding: 0,
      color: '#007bff',
      fontWeight: 'bold',
      fontFamily: 'inherit', // Inherit font from parent
      fontSize: 'inherit', // Inherit font size
    }
  };

  return (
    <div>
      {/* Optional: Basic navigation bar for easy testing */}
      <nav style={styles.nav}>
        <ul style={styles.ul}>
          <li style={styles.li}><Link to="/" style={styles.link}>Home</Link></li>
          {userProfile && appRole === 'superuser' && ( // Condition updated
            <li style={styles.li}><Link to="/admin/tenants" style={styles.link}>Tenant Admin</Link></li>
          )}
          {userProfile && ( // Condition updated to use userProfile
            <li style={{...styles.li, marginLeft: 'auto'}}> {/* Push logout to the right */}
              <button onClick={handleLogout} style={styles.logoutButton}>
                Logout
              </button>
            </li>
          )}
        </ul>
      </nav>

      {/* Define application routes */}
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<HomePage />} />

        {/* Protected Routes for Admin Area */}
        <Route element={<ProtectedRoute />}>
          <Route path="/admin/tenants" element={<TenantListPage />} />
          <Route path="/admin/tenants/new" element={<TenantCreatePage />} />
          <Route path="/admin/tenants/edit/:tenantId" element={<TenantEditPage />} />
          {/* Add other protected admin routes here */}
        </Route>

        <Route path="*" element={<NotFoundPage />} /> {/* Catch-all for 404 */}
      </Routes>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent /> {/* Encapsulate content that needs auth context */}
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
