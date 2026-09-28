import client from './client';
import { EP } from './endpoints';
import { asList, normSubject, normGraph } from './adapters';

export const subjectApi = {
  list: async () => asList((await client.get(EP.subjects.list)).data, ['subjects']).map(normSubject),
  available: async () => asList((await client.get(EP.subjects.available)).data, ['subjects']).map(normSubject),
  get: async (id) => normSubject((await client.get(EP.subjects.byId(id))).data),
  create: async (payload) => normSubject((await client.post(EP.subjects.create, payload)).data),
  enroll: async (id) => normSubject((await client.post(EP.subjects.enroll(id))).data),
  graph: async (id) => normGraph((await client.get(EP.subjects.graph(id))).data),
  approveGraph: async (id) => normSubject((await client.post(EP.subjects.approveGraph(id))).data),
};

