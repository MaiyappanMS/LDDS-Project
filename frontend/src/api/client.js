import axios from 'axios';

export const TOKEN_KEY = 'ldds_token';
const baseURL = import.meta.env.VITE_API_BASE_URL;
if (!baseURL) console.error('VITE_API_BASE_URL is not set. Copy .env.example to .env');

let onUnauthorized = () => {};
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn; };

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

const client = axios.create({ baseURL, timeout: 120000 }); // long: AI calls can be slow

client.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const url = err.config?.url || '';
    const isAuthCall = url.includes('/auth/login') || url.includes('/auth/register');
    if (err.response?.status === 401 && !isAuthCall) onUnauthorized();
    return Promise.reject(err);
  }
);

/** Turn any Axios error into a short, user-safe message (never a stack trace). */
export function apiError(err) {
  if (!err?.response) {
    return err?.code === 'ECONNABORTED'
      ? 'The request took too long. Try again.'
      : 'Cannot reach the server. Check that the backend is running.';
  }
  const { status, data } = err.response;
  const errMsg = typeof data?.error?.message === 'string' ? data.error.message : null;
  const detail = errMsg ?? data?.detail;
  if (status === 401) return typeof detail === 'string' ? detail : 'Your session has expired. Sign in again.';
  if (status === 403) return typeof detail === 'string' ? detail : 'You do not have permission to do that.';
  if (status === 404) return typeof detail === 'string' ? detail : 'We could not find what you asked for.';
  if (status === 422) {
    if (Array.isArray(detail)) return detail.map((d) => `${(d.loc || []).slice(1).join('.') || 'field'}: ${d.msg}`).join('; ');
    return typeof detail === 'string' ? detail : 'Some of the information is invalid.';
  }
  if (status >= 500) return typeof detail === 'string' ? detail : 'Something went wrong on the server. Try again in a moment.';
  return typeof detail === 'string' ? detail : 'Request failed. Try again.';
}

export default client;

