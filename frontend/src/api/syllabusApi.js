import client from './client';
import { EP } from './endpoints';

const normSyllabusRes = (d) => (d?.syllabus ? { ...d.syllabus, ...d } : d);

export const syllabusApi = {
  upload: async (subjectId, file, onProgress) => {
    const form = new FormData();
    form.append('file', file);
    form.append('subject_id', subjectId);
    const { data } = await client.post(EP.syllabus.upload, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded / e.total) * 100)),
    });
    return normSyllabusRes(data);
  },
  get: async (id) => normSyllabusRes((await client.get(EP.syllabus.byId(id))).data),
  forSubject: async (subjectId) => (await client.get(EP.syllabus.bySubject(subjectId))).data,
};

export const STAGES = [
  { key: 'extracting', label: 'Extracting syllabus...' },
  { key: 'analyzing', label: 'Analyzing concepts with AI...' },
  { key: 'building_graph', label: 'Building prerequisite relationships...' },
];

/** Maps whatever status string the backend reports onto the UI stages. */
export const normStage = (status) => {
  const s = String(status || '').toLowerCase();
  if (/(complete|done|success|processed|analyzed)/.test(s)) return 'completed';
  if (/(fail|error)/.test(s)) return 'failed';
  if (/extract/.test(s)) return 'extracting';
  if (/(prereq|graph|relationship)/.test(s)) return 'building_graph';
  if (/(analy|concept|ai)/.test(s)) return 'analyzing';
  return 'processing';
};

