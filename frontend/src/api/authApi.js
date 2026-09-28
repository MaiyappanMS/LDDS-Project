import client from './client';
import { EP } from './endpoints';
import { asList, normUser } from './adapters';

export const extractToken = (d) => d?.access_token ?? d?.token;

export const authApi = {
  register: async (payload) => {
    const body = {
      ...payload,
      full_name: payload.full_name ?? payload.name,
      college_name: payload.college_name ?? payload.college,
    };
    return (await client.post(EP.auth.register, body)).data;
  },
  login: async ({ email, password, role }) => {
    if (import.meta.env.VITE_LOGIN_FORMAT === 'form') {
      const body = new URLSearchParams({ username: email, password });
      return (await client.post(EP.auth.login, body, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })).data;
    }
    return (await client.post(EP.auth.login, { email, password, ...(role ? { role } : {}) })).data;
  },
  me: async () => normUser((await client.get(EP.auth.me)).data),
  colleges: async () => asList((await client.get(EP.colleges.list)).data),
};

