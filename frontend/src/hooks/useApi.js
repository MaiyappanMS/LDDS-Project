import { useCallback, useEffect, useRef, useState } from 'react';
import { apiError } from '../api/client';

// Tiny in-memory cache so revisiting a page does not refetch immediately.
const cache = new Map();
export const invalidate = (prefix) => { for (const k of [...cache.keys()]) if (k.startsWith(prefix)) cache.delete(k); };
export const clearCache = () => cache.clear();

export function useApi(key, fn, { ttl = 30000, enabled = true } = {}) {
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const [state, setState] = useState({ data: null, error: null, loading: enabled });

  const load = useCallback(async (force = false) => {
    if (!enabled) return;
    const hit = key && cache.get(key);
    if (hit && !force && Date.now() - hit.t < ttl) {
      setState({ data: hit.data, error: null, loading: false });
      return;
    }
    setState((p) => ({ ...p, loading: true, error: null }));
    try {
      const data = await fnRef.current();
      if (key) cache.set(key, { data, t: Date.now() });
      setState({ data, error: null, loading: false });
    } catch (e) {
      setState({ data: null, error: apiError(e), loading: false });
    }
  }, [key, ttl, enabled]);

  useEffect(() => { load(); }, [load]);
  return { ...state, reload: () => load(true) };
}

export function useDebounce(value, delay = 300) {
  const [v, setV] = useState(value);
  useEffect(() => { const t = setTimeout(() => setV(value), delay); return () => clearTimeout(t); }, [value, delay]);
  return v;
}
