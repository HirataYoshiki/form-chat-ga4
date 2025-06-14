import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://tdvxprajgxexwhakpdwa.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRkdnhwcmFqZ3hleHdoYWtwZHdhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk2MjYxMjUsImV4cCI6MjA2NTIwMjEyNX0.Mp_XWsSQBvqBeS7ZFNtBXi4LG-ZzJiXCH2vQY-X8OLs';

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Supabase URL and anon key are required.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Example of how to get the current session for later use in AuthContext
// export const getCurrentSession = async () => {
//   const { data: { session }, error } = await supabase.auth.getSession();
//   if (error) {
//     console.error('Error getting session:', error.message);
//     return null;
//   }
//   return session;
// };
