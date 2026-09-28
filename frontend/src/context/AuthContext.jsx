import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, extractToken } from '../api/authApi';
import { setUnauthorizedHandler, tokenStore } from '../api/client';
import { clearCache } from '../hooks/useApi';

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);
export const homeFor = (role) => (role === 'TEACHER' ? '/teacher/dashboard' : '/student/dashboard');

export function AuthProvider({ children }) {
  const navigate = useNavigate();
  const [token, setToken] = useState(tokenStore.get());
  const [currentUser, setUser] = useState(null);
  const [loading, setLoading] = useState(!!tokenStore.get());

  const logout = useCallback(() => {
    tokenStore.clear();
    clearCache();
    setToken(null);
    setUser(null);
  }, []);

  // Any 401 from the API clears auth state and sends the user to login.
  useEffect(() => {
    setUnauthorizedHandler(() => { logout(); navigate('/login?expired=1', { replace: true }); });
  }, [logout, navigate]);

  // Restore session on page load.
  useEffect(() => {
    if (!tokenStore.get()) return;
    authApi.me().then(setUser).catch(logout).finally(() => setLoading(false));
  }, [logout]);

  const login = useCallback(async (credentials) => {
    const data = await authApi.login(credentials);
    const t = extractToken(data);
    if (!t) throw new Error('Login response did not include a token');
    tokenStore.set(t);
    setToken(t);
    const user = await authApi.me(); // role always comes from the backend
    setUser(user);
    return user;
  }, []);

  const value = useMemo(
    () => ({ currentUser, token, role: currentUser?.role ?? null, isAuthenticated: !!currentUser, loading, login, logout }),
    [currentUser, token, loading, login, logout]
  );
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}
