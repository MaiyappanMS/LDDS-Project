import client from './client';
import { EP } from './endpoints';
import { asList, normDebtReport, normPathStep, normStudentOverview, normTeacherOverview } from './adapters';

export const learningDebtApi = {
  forSubject: async (subjectId) => normDebtReport((await client.get(EP.learningDebt.forSubject(subjectId))).data),
  explain: async (subjectId) => normDebtReport((await client.post(EP.learningDebt.explain(subjectId))).data),
  path: async (subjectId) => asList((await client.get(EP.learningDebt.path(subjectId))).data, ['path', 'steps']).map(normPathStep),
  studentOverview: async () => normStudentOverview((await client.get(EP.learningDebt.studentOverview)).data),
  teacherOverview: async () => normTeacherOverview((await client.get(EP.learningDebt.teacherOverview)).data),
};

