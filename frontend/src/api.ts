import axios from 'axios';
import { supabase } from './supabaseClient'; // Make sure this path is correct

const apiClient = axios.create({
  baseURL: '/api/v1', // Adjust if your API is hosted elsewhere
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor for auth tokens
apiClient.interceptors.request.use(
  async (config) => {
    const { data: { session }, error } = await supabase.auth.getSession();

    if (error) {
      console.error('Error getting session for API client:', error.message);
      // Optionally, you could prevent the request or handle the error differently
      // For now, let the request proceed without the token if session fetch fails
      return config;
    }

    if (session && session.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
  },
  (error) => {
    // Do something with request error
    return Promise.reject(error);
  }
);

export default apiClient;
