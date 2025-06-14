import React, { useState, FormEvent, useEffect } from 'react'; // Added useEffect
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false); // Local loading for form submission

  const { login, loading: authLoading, user } = useAuth(); // authLoading from context for session loading
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/admin/tenants'; // Redirect to previous page or default

  // If user is already logged in and tries to access LoginPage, redirect them
  useEffect(() => {
    if (user && !authLoading) {
      navigate(from, { replace: true });
    }
  }, [user, authLoading, navigate, from]);


  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(email, password);
      // Successful login will trigger onAuthStateChange in AuthContext,
      // which will update user state. The useEffect above will handle redirect.
      // Or, navigate directly here if preferred, but AuthContext should ideally be the source of truth.
      // navigate(from, { replace: true }); // This might be redundant if useEffect handles it
    } catch (err: any) {
      console.error('Login failed:', err);
      setError(err.message || 'Failed to login. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  // Basic inline styles
  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '80vh', // Take up most of the viewport height
      padding: '20px',
      fontFamily: 'Arial, sans-serif',
    },
    formWrapper: {
      padding: '30px',
      border: '1px solid #ddd',
      borderRadius: '8px',
      boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
      backgroundColor: '#fff',
      width: '100%',
      maxWidth: '400px',
    },
    heading: {
      textAlign: 'center' as 'center',
      color: '#333',
      marginBottom: '25px'
    },
    formGroup: { marginBottom: '20px' },
    label: {
      display: 'block',
      marginBottom: '8px',
      color: '#555',
      fontSize: '14px'
    },
    input: {
      width: 'calc(100% - 22px)', // Full width minus padding and border
      padding: '12px 10px',
      border: '1px solid #ccc',
      borderRadius: '4px',
      fontSize: '16px',
    },
    button: {
      width: '100%',
      padding: '12px 15px',
      backgroundColor: '#007bff',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      fontSize: '16px',
      cursor: 'pointer',
      opacity: loading ? 0.7 : 1,
      marginTop: '10px',
    },
    error: {
      color: 'red',
      marginBottom: '15px',
      textAlign: 'center' as 'center',
      fontSize: '14px',
    },
  };

  if (authLoading) { // Show loading if AuthContext is still determining auth state
      return <div style={styles.container}><p>Loading session...</p></div>;
  }
  // Do not render form if user is already logged in (useEffect will redirect)
  if (user) {
      return <div style={styles.container}><p>Redirecting...</p></div>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.formWrapper}>
        <h1 style={styles.heading}>Login</h1>
        {error && <p style={styles.error}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <div style={styles.formGroup}>
            <label htmlFor="email" style={styles.label}>Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={styles.input}
              disabled={loading}
            />
          </div>
          <div style={styles.formGroup}>
            <label htmlFor="password" style={styles.label}>Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={styles.input}
              disabled={loading}
            />
          </div>
          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
