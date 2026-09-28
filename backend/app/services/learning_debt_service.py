"""Glue between the database and the deterministic engine in debt_engine.py, plus AI explanations and dashboards."""
import hashlib
import json
import logging
from statistics import mean

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.assessment import Assessment
from app.models.concept import Concept
from app.models.enums import AssessmentStatus
from app.models.learning_debt import LearningDebt
from app.models.mastery import ConceptMastery
from app.models.subject import Subject, SubjectEnrollment
from app.models.user import User
from app.schemas.learning_debt import (
    AssessmentHistoryItem, DebtExplanation, DebtItem, LearningDebtReport, LearningPathResponse,
    LearningPathStep, StudentDashboard, TeacherDashboard, WeakConceptStat,
)
from app.services import ai_service, concept_service, mastery_service, subject_service
from app.services.debt_engine import build_learning_path, detect_learning_debt

logger = logging.getLogger(__name__)


def _graph(db: Session, subject_id: int):
    concepts = concept_service.list_concepts(db, subject_id)
    return {c.id: c.name for c in concepts}, concept_service.get_edges(db, subject_id)


def _explanation_key(item: dict) -> str:
    raw = json.dumps([item["concept_id"], item["mastery"], item["affected_concept_ids"], item["caused_by"]])
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _compute(db: Session, student_id: int, subject_id: int):
    names, edges = _graph(db, subject_id)
    mastery = mastery_service.mastery_map(db, student_id, subject_id)
    items = detect_learning_debt(names, edges, mastery, mastery_service.get_thresholds())
    return names, edges, mastery, items


def recompute_debt(db: Session, student_id: int, subject_id: int) -> list[LearningDebt]:
    """Persist a fresh learning-debt snapshot (keeps cached AI explanations whose inputs are unchanged). No commit."""
    _, _, _, items = _compute(db, student_id, subject_id)
    old = {
        d.concept_id: (d.explanation_key, d.explanation)
        for d in db.scalars(select(LearningDebt).where(
            LearningDebt.student_id == student_id, LearningDebt.subject_id == subject_id))
    }
    db.execute(delete(LearningDebt).where(LearningDebt.student_id == student_id, LearningDebt.subject_id == subject_id))
    rows = []
    for it in items:
        key = _explanation_key(it)
        prev_key, prev_expl = old.get(it["concept_id"], (None, None))
        row = LearningDebt(
            student_id=student_id, subject_id=subject_id, concept_id=it["concept_id"],
            mastery_percentage=it["mastery"], severity=it["severity"], priority_score=it["priority_score"],
            is_root_cause=it["is_root_cause"], affected_concept_ids=it["affected_concept_ids"],
            explanation=prev_expl if prev_key == key else None, explanation_key=key if prev_key == key else None,
        )
        db.add(row)
        rows.append(row)
    db.flush()
    return rows


def _stored_explanations(db: Session, student_id: int, subject_id: int) -> dict[int, tuple[str | None, dict | None]]:
    return {
        d.concept_id: (d.explanation_key, d.explanation)
        for d in db.scalars(select(LearningDebt).where(
            LearningDebt.student_id == student_id, LearningDebt.subject_id == subject_id))
    }


def debt_items(db: Session, student_id: int, subject_id: int) -> list[DebtItem]:
    names, _, _, items = _compute(db, student_id, subject_id)
    stored = _stored_explanations(db, student_id, subject_id)
    result = []
    for it in items:
        key, expl = stored.get(it["concept_id"], (None, None))
        valid_expl = DebtExplanation(**expl) if expl and key == _explanation_key(it) else None
        refs = [{"id": cid, "name": names[cid]} for cid in it["affected_concept_ids"] if cid in names]
        why = (
            valid_expl.why_it_matters
            if valid_expl
            else (
                f"{it['concept']} is a prerequisite for {', '.join(it['affected_concepts'])}."
                if it["affected_concepts"]
                else f"Mastery in {it['concept']} is below threshold ({it['mastery']}%)."
            )
        )
        action = (
            f"Study in order: {' → '.join(valid_expl.recommended_order)}"
            if valid_expl and valid_expl.recommended_order
            else (
                f"Strengthen weak prerequisites first ({', '.join(it['caused_by'])}), then review {it['concept']}."
                if it["caused_by"]
                else f"Review {it['concept']} fundamentals before advancing to dependent concepts."
            )
        )
        result.append(DebtItem(
            concept_id=it["concept_id"], concept=it["concept"], mastery=it["mastery"], severity=it["severity"],
            is_root_cause=it["is_root_cause"], priority_score=it["priority_score"], caused_by=it["caused_by"],
            affected_concepts=it["affected_concepts"],
            affected_concept_refs=refs,
            why_it_matters=why,
            recommended_action=action,
            explanation=valid_expl,
        ))
    return result


def report(db: Session, student_id: int, subject_id: int) -> LearningDebtReport:
    mmap = mastery_service.mastery_map(db, student_id, subject_id)
    overall = round(mean(mmap.values()), 1) if mmap else None
    return LearningDebtReport(
        subject_id=subject_id,
        overall_mastery=overall,
        assessed_concepts=len(mmap),
        debts=debt_items(db, student_id, subject_id),
    )


def explain(db: Session, student_id: int, subject_id: int) -> LearningDebtReport:
    """Generate (and cache) AI explanations for the most urgent debts. Numbers are never changed by the AI."""
    _, _, _, items = _compute(db, student_id, subject_id)
    if not items:
        return report(db, student_id, subject_id)
    recompute_debt(db, student_id, subject_id)  # make sure snapshot rows exist for these items
    rows = {r.concept_id: r for r in db.scalars(select(LearningDebt).where(
        LearningDebt.student_id == student_id, LearningDebt.subject_id == subject_id))}

    for it in items[: settings.max_explanations_per_request]:
        row = rows[it["concept_id"]]
        if row.explanation:  # already cached for identical inputs
            continue
        deterministic_order = it["caused_by"] + [it["concept"]] + it["affected_concepts"]
        payload = {
            "weak_concept": it["concept"], "mastery": it["mastery"], "severity": it["severity"],
            "dependent_concepts": it["affected_concepts"], "weak_prerequisites": it["caused_by"],
        }
        draft = ai_service.explain_learning_debt(payload)
        allowed = set(deterministic_order)
        order = draft.recommended_order
        if not order or any(n not in allowed for n in order):
            order = deterministic_order  # ignore AI ordering that references unknown concepts
        row.explanation = {"summary": draft.summary, "why_it_matters": draft.why_it_matters,
                           "recommended_order": order}
        row.explanation_key = _explanation_key(it)
    db.commit()
    return report(db, student_id, subject_id)


def learning_path(db: Session, student_id: int, subject_id: int) -> LearningPathResponse:
    names, edges = _graph(db, subject_id)
    mastery = mastery_service.mastery_map(db, student_id, subject_id)
    steps = build_learning_path(names, edges, mastery, mastery_service.get_thresholds())
    return LearningPathResponse(subject_id=subject_id, steps=[LearningPathStep(**s) for s in steps])


# ---------------------------------------------------------------- dashboards
def student_dashboard(db: Session, student: User, subject_id: int) -> StudentDashboard:
    subject = subject_service.assert_student_enrolled(db, student, subject_id)
    t = mastery_service.get_thresholds()
    mastery = mastery_service.get_mastery(db, student.id, subject_id)
    debts = debt_items(db, student.id, subject_id)
    history = list(db.scalars(
        select(Assessment).where(Assessment.student_id == student.id, Assessment.subject_id == subject_id,
                                 Assessment.status == AssessmentStatus.COMPLETED)
        .order_by(Assessment.completed_at.desc()).limit(20)))
    hist_items = [
        AssessmentHistoryItem(
            id=a.id, subject_id=subject.id, subject_name=subject.name, status=a.status.value,
            score=a.score, total_questions=a.total_questions, correct_count=a.correct_count,
            started_at=a.started_at, completed_at=a.completed_at,
        )
        for a in history
    ]
    progress = [
        {
            "label": (a.completed_at or a.started_at).strftime("%b %d"),
            "date": (a.completed_at or a.started_at).isoformat(),
            "mastery": a.score or 0,
        }
        for a in reversed(history)
    ]
    return StudentDashboard(
        subject_id=subject_id, subject_name=subject.name,
        overall_mastery=round(mean(m.mastery_percentage for m in mastery), 1) if mastery else None,
        strong_concepts=[m for m in mastery if m.mastery_percentage >= t.developing],
        weak_concepts=[m for m in mastery if m.mastery_percentage < t.moderate_debt],
        learning_debt_count=len(debts),
        high_severity_debt=[d for d in debts if d.severity == "high"],
        learning_path=learning_path(db, student.id, subject_id).steps,
        assessment_history=hist_items,
        recent_assessments=hist_items,
        progress=progress,
    )


def student_overview_dashboard(db: Session, student: User) -> StudentDashboard:
    subjects = subject_service.list_subjects(db, student)
    t = mastery_service.get_thresholds()
    all_mastery: list[MasteryOut] = []
    all_debts: list[DebtItem] = []
    for s in subjects:
        all_mastery.extend(mastery_service.get_mastery(db, student.id, s.id))
        all_debts.extend(debt_items(db, student.id, s.id))

    subj_names = {s.id: s.name for s in subjects}
    history = (
        list(
            db.scalars(
                select(Assessment)
                .where(
                    Assessment.student_id == student.id,
                    Assessment.status == AssessmentStatus.COMPLETED,
                )
                .order_by(Assessment.completed_at.desc())
                .limit(20)
            )
        )
        if subjects
        else []
    )
    hist_items = [
        AssessmentHistoryItem(
            id=a.id,
            subject_id=a.subject_id,
            subject_name=subj_names.get(a.subject_id, ""),
            status=a.status.value,
            score=a.score,
            total_questions=a.total_questions,
            correct_count=a.correct_count,
            started_at=a.started_at,
            completed_at=a.completed_at,
        )
        for a in history
    ]
    progress = [
        {
            "label": (a.completed_at or a.started_at).strftime("%b %d"),
            "date": (a.completed_at or a.started_at).isoformat(),
            "mastery": a.score or 0,
        }
        for a in reversed(history)
    ]
    return StudentDashboard(
        overall_mastery=round(mean(m.mastery_percentage for m in all_mastery), 1) if all_mastery else None,
        strong_concepts=[m for m in all_mastery if m.mastery_percentage >= t.developing],
        weak_concepts=[m for m in all_mastery if m.mastery_percentage < t.moderate_debt],
        learning_debt_count=len(all_debts),
        high_severity_debt=[d for d in all_debts if d.severity == "high"],
        assessment_history=hist_items,
        recent_assessments=hist_items,
        progress=progress,
    )


def _build_teacher_stats(db: Session, subject_ids: list[int], subject_id: int | None = None,
                         subject_name: str | None = None, graph_approved: bool | None = None) -> TeacherDashboard:
    t = mastery_service.get_thresholds()
    if not subject_ids:
        return TeacherDashboard(
            subject_id=subject_id,
            subject_name=subject_name,
            graph_approved=graph_approved,
            total_students=0,
            total_subjects=0,
        )

    enrolled_student_ids = set(
        db.scalars(select(SubjectEnrollment.student_id).where(SubjectEnrollment.subject_id.in_(subject_ids)))
    )
    enrolled_count = len(enrolled_student_ids)

    rows = db.execute(
        select(ConceptMastery.concept_id, Concept.name, ConceptMastery.student_id, ConceptMastery.mastery_percentage)
        .join(Concept, Concept.id == ConceptMastery.concept_id)
        .where(ConceptMastery.subject_id.in_(subject_ids))
    ).all()

    per_concept: dict[int, dict] = {}
    per_student: dict[int, list[float]] = {}
    for cid, name, sid, pct in rows:
        d = per_concept.setdefault(cid, {"name": name, "values": [], "students": set()})
        d["values"].append(pct)
        d["students"].add(sid)
        per_student.setdefault(sid, []).append(pct)

    all_concept_stats = sorted(
        (
            WeakConceptStat(
                concept_id=cid,
                concept=d["name"],
                name=d["name"],
                average_mastery=round(mean(d["values"]), 1),
                students_assessed=len(d["students"]),
                students_weak=sum(1 for v in d["values"] if v < t.moderate_debt),
            )
            for cid, d in per_concept.items()
        ),
        key=lambda s: s.average_mastery,
    )
    weak_stats = [s for s in all_concept_stats if s.average_mastery < t.developing]

    completed_rows = db.execute(
        select(Assessment, User.full_name, Subject.name)
        .join(User, User.id == Assessment.student_id)
        .join(Subject, Subject.id == Assessment.subject_id)
        .where(Assessment.subject_id.in_(subject_ids), Assessment.status == AssessmentStatus.COMPLETED)
        .order_by(Assessment.completed_at.desc())
    ).all()
    completed = [a for a, _, _ in completed_rows]
    scores = [a.score for a in completed if a.score is not None]
    assessment_stats = {
        "completed_assessments": len(completed),
        "average_score": round(mean(scores), 1) if scores else None,
        "highest_score": max(scores) if scores else None,
        "lowest_score": min(scores) if scores else None,
    }

    debts = list(
        db.execute(
            select(LearningDebt, Concept.name)
            .join(Concept, Concept.id == LearningDebt.concept_id)
            .where(LearningDebt.subject_id.in_(subject_ids))
        )
    )
    root_counts: dict[str, int] = {}
    for d, name in debts:
        if d.is_root_cause:
            root_counts[name] = root_counts.get(name, 0) + 1
    high_count = sum(1 for d, _ in debts if d.severity == "high")
    mod_count = sum(1 for d, _ in debts if d.severity == "moderate")
    high_students = len({d.student_id for d, _ in debts if d.severity == "high"})
    debt_stats = {
        "total_debt_items": len(debts),
        "high_severity": high_count,
        "moderate_severity": mod_count,
        "students_with_high_debt": high_students,
        "most_common_root_causes": [
            {"concept": n, "students": c} for n, c in sorted(root_counts.items(), key=lambda kv: -kv[1])[:5]
        ],
    }

    all_values = [v for d in per_concept.values() for v in d["values"]]
    low_count = sum(1 for v in all_values if v >= t.moderate_debt)
    debt_dist = {"high": high_count, "medium": mod_count, "low": low_count} if rows else None

    student_names = (
        dict(db.execute(select(User.id, User.full_name).where(User.id.in_(per_student.keys()))).all())
        if per_student
        else {}
    )
    student_perf = [
        {"id": sid, "name": student_names.get(sid, f"Student {sid}"), "mastery": round(mean(vals), 1)}
        for sid, vals in per_student.items()
    ]
    recent_list = [
        {
            "id": a.id,
            "student_name": sname,
            "subject_name": subj_name,
            "score": a.score,
            "completed_at": a.completed_at,
        }
        for a, sname, subj_name in completed_rows[:15]
    ]

    return TeacherDashboard(
        subject_id=subject_id,
        subject_name=subject_name,
        graph_approved=graph_approved,
        enrolled_students=enrolled_count,
        students_assessed=len(per_student),
        total_students=enrolled_count,
        total_subjects=len(subject_ids),
        average_mastery=round(mean(all_values), 1) if all_values else None,
        high_debt_students=high_students,
        total_assessments=len(completed),
        weak_concepts=weak_stats,
        concept_performance=all_concept_stats,
        debt_distribution=debt_dist,
        student_performance=student_perf,
        recent_assessments=recent_list,
        assessment_stats=assessment_stats,
        learning_debt_stats=debt_stats,
    )


def teacher_dashboard(db: Session, teacher: User, subject_id: int) -> TeacherDashboard:
    subject: Subject = subject_service.assert_teacher_owns(db, teacher, subject_id)
    return _build_teacher_stats(db, [subject_id], subject_id=subject.id, subject_name=subject.name,
                                graph_approved=subject.graph_approved)


def teacher_overview_dashboard(db: Session, teacher: User) -> TeacherDashboard:
    subjects = subject_service.list_subjects(db, teacher)
    return _build_teacher_stats(db, [s.id for s in subjects])

