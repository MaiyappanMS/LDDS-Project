import client from './client';
import { EP } from './endpoints';
import { asList, normConcept } from './adapters';

export const conceptApi = {
  bySubject: async (subjectId) => asList((await client.get(EP.concepts.bySubject(subjectId))).data, ['concepts']).map(normConcept),
  get: async (id) => normConcept((await client.get(EP.concepts.byId(id))).data),
  create: async (payload) => normConcept((await client.post(EP.concepts.create, payload)).data),
  update: async (id, payload) => (await client.put(EP.concepts.byId(id), payload)).data,
  remove: async (id) => (await client.delete(EP.concepts.byId(id))).data,
  addPrerequisite: async (id, prerequisiteId) => (await client.post(EP.concepts.addPrereq(id), { prerequisite_id: prerequisiteId })).data,
  removePrerequisite: async (id, prerequisiteId) => (await client.delete(EP.concepts.removePrereq(id, prerequisiteId))).data,
};
