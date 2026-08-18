import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { login as apiLogin, register as apiRegister } from '../api/client';

const AuthContext = createContext(null);

function decodeToken(token) {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
  } catch {
    return null;
  }
}

function loadStoredUser() {
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [user, setUser] = useState(() => loadStoredUser());

  const persistSession = useCallback((accessToken, userInfo) => {
    localStorage.setItem('token', accessToken);
    localStorage.setItem('user', JSON.stringify(userInfo));
    setToken(accessToken);
    setUser(userInfo);
  }, []);

  const login = useCallback(async (email, password) => {
    const { data } = await apiLogin(email, password);
    const decoded = decodeToken(data.access_token);
    const userInfo = {
      email: decoded?.email ?? email,
      name: decoded?.name ?? email.split('@')[0],
    };
    persistSession(data.access_token, userInfo);
    return userInfo;
  }, [persistSession]);

  const register = useCallback(async (name, email, password) => {
    const { data } = await apiRegister(name, email, password);
    persistSession(data.access_token, { name, email });
    return { name, email };
  }, [persistSession]);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      login,
      register,
      logout,
    }),
    [token, user, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
