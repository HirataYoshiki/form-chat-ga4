import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { Session, User as SupabaseUser } from '@supabase/supabase-js'; // Renamed User to SupabaseUser to avoid clash
import { supabase } from '../supabaseClient';
import apiClient from '../api'; // Import apiClient

// Interface for our backend's user profile
export interface AuthenticatedUserProfile {
  id: string;
  app_role: string;
  tenant_id: string | null;
  email: string | null;
  full_name: string | null;
  // Add any other fields from backend AuthenticatedUser if needed
}

interface AuthContextType {
  session: Session | null; // Supabase session
  supabaseUser: SupabaseUser | null; // Supabase's raw user object
  userProfile: AuthenticatedUserProfile | null; // Profile from our /users/me
  appRole: string | null;
  authLoading: boolean; // True while session or profile is loading
  login: (email?: string, password?: string) => Promise<any>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [supabaseUser, setSupabaseUser] = useState<SupabaseUser | null>(null);
  const [userProfile, setUserProfile] = useState<AuthenticatedUserProfile | null>(null);
  const [appRole, setAppRole] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  const fetchUserProfile = useCallback(async () => {
    // This function is called when a session is confirmed
    try {
      const { data } = await apiClient.get<AuthenticatedUserProfile>('/users/me');
      setUserProfile(data);
      setAppRole(data.app_role);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      // Could sign out here if profile is essential
      // await supabase.auth.signOut();
      setUserProfile(null); // Clear profile on error
      setAppRole(null);
    }
  }, []);

  useEffect(() => {
    setAuthLoading(true);
    const getInitialSessionAndProfile = async () => {
      const { data: { session: currentSession }, error } = await supabase.auth.getSession();
      if (error) {
        console.error("Error getting initial session:", error.message);
      }
      setSession(currentSession);
      setSupabaseUser(currentSession?.user ?? null);
      if (currentSession) {
        await fetchUserProfile();
      }
      setAuthLoading(false);
    };

    getInitialSessionAndProfile();

    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (_event, currentSession) => {
        setAuthLoading(true);
        setSession(currentSession);
        setSupabaseUser(currentSession?.user ?? null);
        if (currentSession) {
          await fetchUserProfile();
        } else {
          // Logged out
          setUserProfile(null);
          setAppRole(null);
        }
        setAuthLoading(false);
      }
    );

    return () => {
      authListener?.unsubscribe();
    };
  }, [fetchUserProfile]);

  const login = async (email?: string, password?: string) => {
    if (!email || !password) throw new Error("Email and password are required for login.");
    setAuthLoading(true); // Indicate loading
    // Supabase signIn will trigger onAuthStateChange, which then fetches profile
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      setAuthLoading(false); // Reset loading on error
      throw error;
    }
    // onAuthStateChange will handle setting session, user, profile, and final authLoading state
    return data;
  };

  const logout = async () => {
    setAuthLoading(true); // Indicate loading
    await supabase.auth.signOut();
    // onAuthStateChange will clear session, user, profile and set authLoading to false
  };

  const value = {
    session,
    supabaseUser,
    userProfile,
    appRole,
    authLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
