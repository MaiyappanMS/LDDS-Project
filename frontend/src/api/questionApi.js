import client from './client';
import { EP } from './endpoints';
import { asList, normQuestion } from './adapters';

export const questionApi = {
  generate: async ({ subjectId, conceptId, count, difficulty }) => {
    const { data } = await client.post(EP.questions.generate, {
      subject_id: subjectId,
      concept_id: conceptId,
      number_of_questions: count,
      num_questions: count,
      difficulty,
    });
    return asList(data, ['questions']).map(normQuestion);
  },
  bySubject: async (subjectId) =>
    asList((await client.get(EP.questions.bySubject(subjectId))).data, ['questions']).map(normQuestion),
  byConcept: async (conceptId) =>
    asList((await client.get(EP.questions.byConcept(conceptId))).data, ['questions']).map(normQuestion),
};

