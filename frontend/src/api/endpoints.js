// SINGLE source of truth for backend paths. Change paths here only.
export const EP = {
  auth: { register: '/auth/register', login: '/auth/login', me: '/auth/me' },
  colleges: { list: '/colleges' },
  subjects: {
    list: '/subjects',
    available: '/subjects/available',
    create: '/subjects',
    byId: (id) => `/subjects/${id}`,
    enroll: (id) => `/subjects/${id}/enroll`,
    graph: (id) => `/subjects/${id}/knowledge-graph`,
    approveGraph: (id) => `/subjects/${id}/approve-graph`,
  },
  syllabus: {
    upload: '/syllabus/upload',
    byId: (id) => `/syllabus/${id}`,
    bySubject: (subjectId) => `/syllabus/subject/${subjectId}`,
  },
  concepts: {
    bySubject: (subjectId) => `/concepts/subject/${subjectId}`,
    create: '/concepts',
    byId: (id) => `/concepts/${id}`,
    addPrereq: (id) => `/concepts/${id}/prerequisites`,
    removePrereq: (id, prereqId) => `/concepts/${id}/prerequisites/${prereqId}`,
  },
  questions: {
    generate: '/questions/generate',
    bySubject: (subjectId) => `/questions/subject/${subjectId}`,
    byConcept: (conceptId) => `/questions/concept/${conceptId}`,
  },
  assessments: {
    create: '/assessments',
    byId: (id) => `/assessments/${id}`,
    questions: (id) => `/assessments/${id}/questions`,
    submit: (id) => `/assessments/${id}/submit`,
  },
  learningDebt: {
    forSubject: (subjectId) => `/students/me/learning-debt/${subjectId}`,
    explain: (subjectId) => `/students/me/learning-debt/${subjectId}/explain`,
    studentOverview: '/students/me/dashboard',
    teacherOverview: '/teachers/me/dashboard',
    path: (subjectId) => `/students/me/learning-path/${subjectId}`,
  },
};

