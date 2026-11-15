// src/context/AuthContext.jsx
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AUTH_TOKEN_KEY, AUTH_USER_KEY } from '../services/api';
import {
  getCurrentUser,
  loginUser,
  logoutUser,
  signupStudent,
} from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const cached = localStorage.getItem(AUTH_USER_KEY);
      return cached ? JSON.parse(cached) : null;
    } catch {
      return null;
    }
  });
  const [authLoading, setAuthLoading] = useState(() => {
    return Boolean(localStorage.getItem(AUTH_TOKEN_KEY));
  });

  const clearAuthStorage = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    setUser(null);
  }, []);

  // Rehydrate & verify session on page refresh
  useEffect(() => {
    let active = true;
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    if (!token) {
      setUser(null);
      setAuthLoading(false);
      return;
    }

    async function hydrateSession() {
      try {
        const res = await getCurrentUser();
        if (active && res?.user) {
          setUser(res.user);
          localStorage.setItem(AUTH_USER_KEY, JSON.stringify(res.user));
        } else if (active) {
          clearAuthStorage();
        }
      } catch {
        if (active) {
          clearAuthStorage();
        }
      } finally {
        if (active) {
          setAuthLoading(false);
        }
      }
    }

    hydrateSession();
    return () => {
      active = false;
    };
  }, [clearAuthStorage]);

  // Listen for 401 unauthorized events from fetchAPI
  useEffect(() => {
    const handleUnauthorized = () => {
      clearAuthStorage();
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [clearAuthStorage]);

  const login = async (username, password) => {
    const res = await loginUser({ username, password });
    if (res?.access_token && res?.user) {
      localStorage.setItem(AUTH_TOKEN_KEY, res.access_token);
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(res.user));
      setUser(res.user);
    }
    return res;
  };

  const signup = async ({ username, password, full_name = null, class_id = null }) => {
    const res = await signupStudent({ username, password, full_name, class_id });
    if (res?.access_token && res?.user) {
      localStorage.setItem(AUTH_TOKEN_KEY, res.access_token);
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(res.user));
      setUser(res.user);
    }
    return res;
  };

  const logout = async () => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      await logoutUser().catch(() => {});
    }
    clearAuthStorage();
  };

  const isAuthenticated = Boolean(user);
  const isAdmin = user?.role === 'admin';
  const isStudent = user?.role === 'user';

  return (
    <AuthContext.Provider
      value={{
        user,
        authLoading,
        isAuthenticated,
        isAdmin,
        isStudent,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider.');
  }
  return ctx;
}
