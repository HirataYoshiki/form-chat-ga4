import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import TenantListPage from './components/TenantListPage';
import TenantCreatePage from './components/TenantCreatePage';
import TenantEditPage from './components/TenantEditPage';

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


const App: React.FC = () => {
  // Basic inline styles for the app layout
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
    },
    li: {
      marginRight: '15px',
    },
    link: {
      textDecoration: 'none',
      color: '#007bff',
      fontWeight: 'bold',
    }
  };

  return (
    <BrowserRouter>
      <div>
        {/* Optional: Basic navigation bar for easy testing */}
        <nav style={styles.nav}>
          <ul style={styles.ul}>
            <li style={styles.li}><Link to="/" style={styles.link}>Home</Link></li>
            <li style={styles.li}><Link to="/admin/tenants" style={styles.link}>Tenant Admin</Link></li>
          </ul>
        </nav>

        {/* Define application routes */}
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/admin/tenants" element={<TenantListPage />} />
          <Route path="/admin/tenants/new" element={<TenantCreatePage />} />
          <Route path="/admin/tenants/edit/:tenantId" element={<TenantEditPage />} />
          {/* Add other routes here */}
          <Route path="*" element={<NotFoundPage />} /> {/* Catch-all for 404 */}
        </Routes>
      </div>
    </BrowserRouter>
  );
};

export default App;
