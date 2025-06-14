import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1', // Adjust if your API is hosted elsewhere
  headers: {
    'Content-Type': 'application/json',
  },
});

// Example of how to add a request interceptor for auth tokens later
// apiClient.interceptors.request.use(config => {
//   const token = localStorage.getItem('authToken'); // Or however you store your token
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

export default apiClient;
