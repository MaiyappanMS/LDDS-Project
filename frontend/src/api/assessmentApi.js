import client from './client';
import { EP } from './endpoints';
import { asList, normQuestion, normResult } from './adapters';

export const assessmentApi = {
  create: async (subjectId) => {
    const { data } = await client.post(EP.assessments.create, { subject_id: subjectId });
    return data?.id ?? data?.assessment_id;
  },
  get: async (id) => normResult((await client.get(EP.assessments.byId(id))).data),
  questions: async (id) => asList((await client.get(EP.assessments.questions(id))).data, ['questions']).map(normQuestion),
  // answers: { [questionId]: optionKey }. The payload shape is isolated here.
  submit: async (id, answers) => {
    const payload = {
      answers: Object.entries(answers).map(([qid, selected_option]) => ({
        question_id: Number.isNaN(Number(qid)) ? qid : Number(qid),
        selected_answer: selected_option,
        selected_option,
      })),
    };
    return normResult((await client.post(EP.assessments.submit(id), payload)).data);
  },
};

