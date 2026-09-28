"""Concept CRUD + knowledge graph (prerequisite edges, cycle protection)."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, CircularDependencyError, ConflictError, NotFoundError
from app.models.concept import Concept, ConceptDependency
from app.models.enums import Difficulty
from app.models.subject import Subject
from app.schemas.concept import (
    ConceptCreate, ConceptOut, ConceptRef, ConceptUpdate, GraphEdge, GraphNode, KnowledgeGraph,
)
from app.services.graph_utils import would_create_cycle


def get_concept(db: Session, concept_id: int) -> Concept:
    concept = db.get(Concept, concept_id)
    if not concept:
        raise NotFoundError("Concept not found.")
    return concept


def list_concepts(db: Session, subject_id: int) -> list[Concept]:
    return list(db.scalars(select(Concept).where(Concept.subject_id == subject_id).order_by(Concept.position, Concept.id)))


def get_edges(db: Session, subject_id: int) -> list[tuple[int, int]]:
    """All edges of a subject as (prerequisite_id, concept_id)."""
    stmt = (
        select(ConceptDependency.prerequisite_id, ConceptDependency.concept_id)
        .join(Concept, Concept.id == ConceptDependency.concept_id)
        .where(Concept.subject_id == subject_id)
    )
    return [(p, c) for p, c in db.execute(stmt)]


def serialize(concept: Concept, db: Session | None = None, user=None) -> ConceptOut:
    from app.models.enums import UserRole

    prereqs = [ConceptRef(id=l.prerequisite.id, name=l.prerequisite.name) for l in concept.prerequisite_links]
    deps = [ConceptRef(id=l.concept.id, name=l.concept.name) for l in concept.dependent_links]
    approved = concept.subject.graph_approved if concept.subject else None

    mastery_val: float | None = None
    explanation_text: str | None = None
    debt_dict: dict | None = None

    if db is not None and user is not None and getattr(user, "role", None) == UserRole.STUDENT:
        from app.services import learning_debt_service, mastery_service

        mmap = mastery_service.mastery_map(db, user.id, concept.subject_id)
        mastery_val = mmap.get(concept.id)
        debts = learning_debt_service.debt_items(db, user.id, concept.subject_id)
        match = next((d for d in debts if d.concept_id == concept.id), None)
        if match:
            expl = match.explanation
            why = (
                expl.why_it_matters
                if expl
                else (
                    f"{concept.name} is a foundational prerequisite for {', '.join(match.affected_concepts)}."
                    if match.affected_concepts
                    else f"Your current mastery in {concept.name} is {match.mastery}%, which needs reinforcement."
                )
            )
            action = (
                f"Study in order: {' → '.join(expl.recommended_order)}"
                if expl and expl.recommended_order
                else (
                    f"Review weak prerequisites first ({', '.join(match.caused_by)}), then practice {concept.name}."
                    if match.caused_by
                    else f"Review {concept.name} core concepts and retake a practice assessment."
                )
            )
            debt_dict = {
                "concept_id": match.concept_id,
                "concept_name": match.concept,
                "mastery": match.mastery,
                "severity": match.severity,
                "why_it_matters": why,
                "recommended_action": action,
                "affected_concepts": [r.model_dump() for r in deps],
            }
            explanation_text = f"{expl.summary}\n\n{expl.why_it_matters}" if expl else f"{concept.description or ''}\n\n{why}".strip()
        else:
            parts = []
            if concept.description:
                parts.append(concept.description)
            if prereqs:
                parts.append(f"Builds upon: {', '.join(p.name for p in prereqs)}.")
            if deps:
                parts.append(f"Unlocks later concepts: {', '.join(d.name for d in deps)}.")
            explanation_text = "\n\n".join(parts) if parts else None

    return ConceptOut(
        id=concept.id,
        subject_id=concept.subject_id,
        name=concept.name,
        description=concept.description,
        difficulty=concept.difficulty,
        is_ai_generated=concept.is_ai_generated,
        is_approved=approved,
        prerequisites=prereqs,
        dependents=deps,
        mastery=mastery_val,
        ai_explanation=explanation_text,
        learning_debt=debt_dict,
    )



def _find_by_name(db: Session, subject_id: int, name: str) -> Concept | None:
    return db.scalar(select(Concept).where(Concept.subject_id == subject_id, func.lower(Concept.name) == name.strip().lower()))


def _next_position(db: Session, subject_id: int) -> int:
    return (db.scalar(select(func.max(Concept.position)).where(Concept.subject_id == subject_id)) or 0) + 1


def create_concept(db: Session, subject: Subject, data: ConceptCreate, *, ai_generated: bool = False,
                   syllabus_id: int | None = None, commit: bool = True) -> Concept:
    name = data.name.strip()
    if _find_by_name(db, subject.id, name):
        raise ConflictError(f"A concept named '{name}' already exists in this subject.")
    concept = Concept(
        subject_id=subject.id, syllabus_id=syllabus_id, name=name, description=data.description,
        difficulty=data.difficulty, is_ai_generated=ai_generated, position=_next_position(db, subject.id),
    )
    db.add(concept)
    db.flush()
    for pid in data.prerequisite_ids:
        add_prerequisite(db, concept, pid, commit=False)
    if commit:
        db.commit()
        db.refresh(concept)
    return concept


def update_concept(db: Session, concept: Concept, data: ConceptUpdate) -> Concept:
    if data.name is not None:
        new_name = data.name.strip()
        clash = _find_by_name(db, concept.subject_id, new_name)
        if clash and clash.id != concept.id:
            raise ConflictError(f"A concept named '{new_name}' already exists in this subject.")
        concept.name = new_name
    if data.description is not None:
        concept.description = data.description
    if data.difficulty is not None:
        concept.difficulty = data.difficulty
    db.commit()
    db.refresh(concept)
    return concept


def delete_concept(db: Session, concept: Concept) -> None:
    db.delete(concept)
    db.commit()


def add_prerequisite(db: Session, concept: Concept, prerequisite_id: int, *, ai_proposed: bool = False,
                     commit: bool = True) -> ConceptDependency:
    if prerequisite_id == concept.id:
        raise AppError("A concept cannot be its own prerequisite.", error_code="invalid_relationship")
    prereq = get_concept(db, prerequisite_id)
    if prereq.subject_id != concept.subject_id:
        raise AppError("Prerequisite must belong to the same subject.", error_code="invalid_relationship")
    exists = db.scalar(select(ConceptDependency.id).where(
        ConceptDependency.concept_id == concept.id, ConceptDependency.prerequisite_id == prereq.id))
    if exists:
        raise ConflictError("This prerequisite relationship already exists.", error_code="duplicate_relationship")
    if would_create_cycle(prereq.id, concept.id, get_edges(db, concept.subject_id)):
        raise CircularDependencyError(
            f"Rejected: making '{prereq.name}' a prerequisite of '{concept.name}' would create a circular dependency.")
    link = ConceptDependency(concept_id=concept.id, prerequisite_id=prereq.id, is_ai_proposed=ai_proposed)
    db.add(link)
    db.flush()
    if commit:
        db.commit()
        db.refresh(link)
    return link


def remove_prerequisite(db: Session, concept: Concept, prerequisite_id: int) -> None:
    link = db.scalar(select(ConceptDependency).where(
        ConceptDependency.concept_id == concept.id, ConceptDependency.prerequisite_id == prerequisite_id))
    if not link:
        raise NotFoundError("Prerequisite relationship not found.")
    db.delete(link)
    db.commit()


def knowledge_graph(db: Session, subject: Subject, user=None) -> KnowledgeGraph:
    from app.models.enums import UserRole
    from app.services import mastery_service

    concepts = list_concepts(db, subject.id)
    mmap = (
        mastery_service.mastery_map(db, user.id, subject.id)
        if user is not None and getattr(user, "role", None) == UserRole.STUDENT
        else {}
    )
    return KnowledgeGraph(
        subject_id=subject.id,
        graph_approved=subject.graph_approved,
        nodes=[
            GraphNode(
                id=c.id, name=c.name, description=c.description, difficulty=c.difficulty, mastery=mmap.get(c.id)
            )
            for c in concepts
        ],
        edges=[GraphEdge(source=p, target=c) for p, c in get_edges(db, subject.id)],
    )



def approve_graph(db: Session, subject: Subject) -> Subject:
    if not list_concepts(db, subject.id):
        raise AppError("Add or extract at least one concept before approving the graph.")
    subject.graph_approved = True
    db.commit()
    db.refresh(subject)
    return subject


def save_analysis(db: Session, subject: Subject, syllabus_id: int, concepts: list[dict]) -> tuple[int, int, list[str]]:
    """Persist validated AI output. Existing concept names are reused; edges that would create
    cycles are skipped and reported as warnings. Returns (concepts_created, edges_created, warnings)."""
    warnings: list[str] = []
    by_name: dict[str, Concept] = {}
    created = 0
    for item in concepts:
        existing = _find_by_name(db, subject.id, item["name"])
        if existing:
            by_name[item["name"].lower()] = existing
            continue
        concept = Concept(
            subject_id=subject.id, syllabus_id=syllabus_id, name=item["name"].strip(),
            description=item.get("description"), difficulty=Difficulty(item["difficulty"]),
            is_ai_generated=True, position=_next_position(db, subject.id),
        )
        db.add(concept)
        db.flush()
        by_name[item["name"].lower()] = concept
        created += 1

    edges_created = 0
    for item in concepts:
        concept = by_name[item["name"].lower()]
        for pre_name in item.get("prerequisites", []):
            prereq = by_name.get(pre_name.lower())
            if prereq is None:
                warnings.append(f"Ignored unknown prerequisite '{pre_name}' for '{concept.name}'.")
                continue
            try:
                add_prerequisite(db, concept, prereq.id, ai_proposed=True, commit=False)
                edges_created += 1
            except ConflictError as exc:
                warnings.append(f"Skipped '{prereq.name}' -> '{concept.name}': {exc.message}")
            except AppError as exc:
                warnings.append(f"Skipped '{prereq.name}' -> '{concept.name}': {exc.message}")
    db.commit()
    return created, edges_created, warnings
