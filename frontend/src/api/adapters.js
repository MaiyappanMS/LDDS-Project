// ADAPTER LAYER: the only place that knows backend response shapes.
// If the backend differs from what is assumed here, fix it in this file.

export const asList = (d, extra = []) => {
  if (Array.isArray(d)) return d;
  for (const k of ['items', 'results', 'data', ...extra]) if (Array.isArray(d?.[k])) return d[k];
  return [];
};

// Mastery may come as a 0-1 fraction or 0-100. Values <= 1 are treated as fractions.
export const pct = (v) => {
  const n = Number(v);
  if (!Number.isFinite(n)) return 0;
  return Math.round(n <= 1 ? n * 100 : n);
};

export const severityFromMastery = (m) => (m < 40 ? 'HIGH' : m < 60 ? 'MEDIUM' : 'LOW');
export const normSeverity = (s, mastery) => {
  const v = String(s || '').toUpperCase();
  if (['HIGH', 'MEDIUM', 'LOW'].includes(v)) return v;
  if (v === 'MODERATE') return 'MEDIUM';
  if (v === 'CRITICAL' || v === 'SEVERE') return 'HIGH';
  return severityFromMastery(mastery);
};

const ref = (p) =>
  p && typeof p === 'object'
    ? { id: p.id ?? p.concept_id ?? p.prerequisite_id, name: p.name ?? p.title ?? p.concept }
    : typeof p === 'string' && Number.isNaN(Number(p))
      ? { id: undefined, name: p }
      : { id: p, name: undefined };

export const normUser = (u) => ({
  id: u?.id,
  name: u?.name ?? u?.full_name ?? u?.username ?? '',
  email: u?.email ?? '',
  role: String(u?.role ?? '').toUpperCase(),
  college: u?.college ?? u?.college_name ?? '',
  collegeId: u?.college_id ?? null,
  stats: u?.stats ?? null,
});

export const normSubject = (s) => ({
  id: s.id,
  name: s.name ?? s.title,
  description: s.description ?? '',
  semester: s.semester ?? '',
  graphApproved: Boolean(s.graph_approved),
  studentCount: s.student_count ?? s.students_count ?? (Array.isArray(s.students) ? s.students.length : undefined),
  conceptCount: s.concept_count ?? s.concepts_count ?? (Array.isArray(s.concepts) ? s.concepts.length : undefined),
  students: Array.isArray(s.students)
    ? s.students.map((u) => ({ id: u.id, name: u.name ?? u.full_name, email: u.email, mastery: u.mastery != null ? pct(u.mastery) : null }))
    : [],
  stats: s.assessment_stats ?? s.stats ?? null,
  mastery: s.mastery != null ? pct(s.mastery) : s.overall_mastery != null ? pct(s.overall_mastery) : null,
});

export const normConcept = (c) => ({
  id: c.id,
  subjectId: c.subject_id ?? c.subject?.id,
  name: c.name ?? c.title,
  description: c.description ?? '',
  difficulty: String(c.difficulty ?? c.difficulty_level ?? 'beginner').toLowerCase(),
  status: c.status ?? (c.is_approved ? 'approved' : c.is_approved === false ? 'needs review' : 'ai generated'),
  prerequisites: (c.prerequisites ?? c.prerequisite_ids ?? []).map(ref),
  dependents: (c.dependents ?? c.dependent_concepts ?? []).map(ref),
  mastery: c.mastery != null ? pct(c.mastery) : c.mastery_score != null ? pct(c.mastery_score) : null,
  explanation: c.ai_explanation ?? (typeof c.explanation === 'string' ? c.explanation : '') ?? '',
  debt: c.learning_debt ?? c.debt ?? null,
});

export const normGraph = (g) => {
  const rawNodes = asList(g?.nodes ?? g?.concepts ?? g);
  const nodes = rawNodes.map((n) => ({
    id: n.id,
    name: n.name ?? n.label ?? n.title,
    description: n.description ?? '',
    difficulty: String(n.difficulty ?? 'beginner').toLowerCase(),
    mastery: n.mastery != null ? pct(n.mastery) : null,
  }));
  let edges = asList(g?.edges ?? g?.links).map((e) => ({
    source: e.source ?? e.from ?? e.prerequisite_id,
    target: e.target ?? e.to ?? e.concept_id,
  }));
  if (!edges.length) {
    rawNodes.forEach((n) => (n.prerequisites ?? []).forEach((p) => edges.push({ source: ref(p).id, target: n.id })));
  }
  return { nodes, edges, graphApproved: Boolean(g?.graph_approved) };
};

export const normDebt = (d) => {
  const mastery = pct(d.mastery ?? d.mastery_percentage ?? d.mastery_score ?? d.score);
  const conceptName = d.concept_name ?? d.name ?? (typeof d.concept === 'string' ? d.concept : d.concept?.name);
  const explObj = d.explanation && typeof d.explanation === 'object' ? d.explanation : null;
  const explStr = typeof d.explanation === 'string' ? d.explanation : '';
  const affectedList = d.affected_concept_refs?.length
    ? d.affected_concept_refs
    : (d.affected_concepts ?? d.affects ?? d.dependents ?? []);
  const reason = d.why_it_matters ?? explObj?.why_it_matters ?? explObj?.summary ?? d.reason ?? explStr ?? '';
  const action = d.recommended_action ?? d.action ?? (
    explObj?.recommended_order?.length
      ? `Study in order: ${explObj.recommended_order.join(' → ')}`
      : ''
  );
  return {
    conceptId: d.concept_id ?? d.id,
    name: conceptName,
    mastery,
    severity: normSeverity(d.severity ?? d.debt_level, mastery),
    reason,
    affected: affectedList.map(ref),
    action,
  };
};

export const normDebtReport = (r) => ({
  items: asList(r, ['debts', 'learning_debts', 'weak_concepts']).map(normDebt),
  overallMastery: r?.overall_mastery != null ? pct(r.overall_mastery) : null,
});

export const normPathStep = (s, i) => {
  const mastery = pct(s.mastery ?? s.mastery_percentage ?? s.mastery_score);
  const raw = String(s.status ?? '').toLowerCase().replace(/\s+/g, '_');
  const statusMap = {
    high_debt: 'needs_review',
    moderate_debt: 'needs_review',
    developing: 'in_progress',
    mastered: 'mastered',
  };
  const status = ['locked', 'in_progress', 'needs_review', 'mastered'].includes(raw)
    ? raw
    : statusMap[raw] ?? (mastery >= 80 ? 'mastered' : mastery < 60 ? 'needs_review' : 'in_progress');
  return {
    conceptId: s.concept_id ?? s.id,
    step: s.step ?? s.order ?? i + 1,
    name: s.concept_name ?? s.name ?? (typeof s.concept === 'string' ? s.concept : s.concept?.name),
    mastery,
    severity: normSeverity(s.severity, mastery),
    reason: s.reason ?? s.why ?? s.why_recommended ?? '',
    status,
  };
};

export const normQuestion = (q) => {
  let options = q.options ?? q.choices ?? [];
  if (!Array.isArray(options) && typeof options === 'object') {
    options = Object.entries(options).map(([key, text]) => ({ key, text }));
  } else {
    options = options.map((o, i) =>
      typeof o === 'string'
        ? { key: String.fromCharCode(65 + i), text: o }
        : { key: o.key ?? o.id ?? String.fromCharCode(65 + i), text: o.text ?? o.label }
    );
  }
  return {
    id: q.id,
    text: q.question_text ?? q.question ?? q.text,
    options,
    correct: q.correct_answer ?? q.correct_option ?? null, // teacher views only
    explanation: q.explanation ?? '',
    difficulty: String(q.difficulty ?? '').toLowerCase(),
    conceptId: q.concept_id ?? q.concept?.id,
    conceptName: q.concept_name ?? q.concept?.name ?? '',
  };
};

export const normResult = (r) => {
  const base = r?.assessment ?? r;
  const rawConcepts = r?.concept_scores ?? r?.mastery ?? r?.concept_performance ?? r?.concepts ?? base?.concept_scores ?? [];
  const concepts = asList(rawConcepts, ['concept_mastery']).map((c) => ({
    id: c.concept_id ?? c.id,
    name: c.concept_name ?? (typeof c.concept === 'string' ? c.concept : c.concept?.name) ?? c.name,
    mastery: pct(c.mastery_percentage ?? c.mastery ?? c.score ?? c.percentage),
  }));
  const total = base?.total_questions ?? base?.total ?? 0;
  const correct = base?.correct_answers ?? base?.correct ?? base?.correct_count ?? 0;
  const overall = r?.overall_mastery ?? base?.overall_mastery ?? (
    concepts.length ? Math.round(concepts.reduce((s, c) => s + c.mastery, 0) / concepts.length) : null
  );
  return {
    id: base?.id ?? base?.assessment_id,
    subjectId: base?.subject_id ?? base?.subject?.id,
    status: base?.status,
    score: base?.score != null ? pct(base.score) : total ? Math.round((correct / total) * 100) : 0,
    overallMastery: overall != null ? pct(overall) : null,
    total,
    correct,
    incorrect: base?.incorrect_answers ?? base?.incorrect ?? (total ? total - correct : 0),
    concepts,
  };
};

const normAssessmentRow = (a) => ({
  id: a.id ?? a.assessment_id,
  subject: a.subject_name ?? a.subject?.name ?? '',
  student: a.student_name ?? a.student?.name ?? '',
  score: a.score != null ? pct(a.score) : null,
  date: a.completed_at ?? a.submitted_at ?? a.started_at ?? a.created_at ?? a.date ?? '',
});
const normConceptStat = (c) => ({
  id: c.concept_id ?? c.id,
  name: c.concept_name ?? c.name ?? (typeof c.concept === 'string' ? c.concept : c.concept?.name),
  mastery: pct(c.mastery ?? c.mastery_percentage ?? c.average_mastery ?? c.score),
});

export const normStudentOverview = (o) => ({
  overallMastery: o?.overall_mastery != null ? pct(o.overall_mastery) : null,
  debtCount: o?.learning_debt_count ?? o?.debt_count ?? null,
  strong: asList(o?.strong_concepts).map(normConceptStat),
  weak: asList(o?.weak_concepts).map(normConceptStat),
  recent: asList(o?.recent_assessments ?? o?.assessment_history).map(normAssessmentRow),
  progress: asList(o?.progress).map((p) => ({ name: p.label ?? p.date ?? p.name, mastery: pct(p.mastery ?? p.value) })),
});

export const normTeacherOverview = (o) => ({
  totalStudents: o?.total_students ?? o?.enrolled_students ?? null,
  totalSubjects: o?.total_subjects ?? null,
  avgMastery: o?.average_mastery != null ? pct(o.average_mastery) : o?.avg_mastery != null ? pct(o.avg_mastery) : null,
  highDebtStudents: o?.high_debt_students ?? o?.students_with_high_debt ?? o?.learning_debt_stats?.students_with_high_debt ?? null,
  assessmentCount: o?.total_assessments ?? o?.assessment_count ?? o?.assessment_stats?.completed_assessments ?? null,
  weakConcepts: asList(o?.weakest_concepts ?? o?.weak_concepts).map(normConceptStat),
  concepts: asList(o?.concept_performance).map(normConceptStat),
  debtDistribution: o?.debt_distribution ?? null, // { high, medium, low }
  studentPerformance: asList(o?.student_performance).map((s) => ({ name: s.name ?? s.student_name, mastery: pct(s.mastery ?? s.average_mastery) })),
  recent: asList(o?.recent_assessments).map(normAssessmentRow),
});

