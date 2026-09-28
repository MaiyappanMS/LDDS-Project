from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_teacher
from app.core.exceptions import ForbiddenError
from app.database.connection import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.concept import ConceptCreate, ConceptOut, ConceptUpdate, PrerequisiteCreate
from app.services import concept_service, subject_service

router = APIRouter(prefix="/api/concepts", tags=["Concepts"])


@router.post("", response_model=ConceptOut, status_code=status.HTTP_201_CREATED,
             summary="Teacher: add a concept manually")
def create_concept(data: ConceptCreate, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    subject = subject_service.assert_teacher_owns(db, teacher, data.subject_id)
    return concept_service.serialize(concept_service.create_concept(db, subject, data), db=db, user=teacher)


@router.get("/subject/{subject_id}", response_model=list[ConceptOut], summary="List concepts of a subject")
def list_concepts(subject_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject = subject_service.assert_can_view(db, user, subject_id)
    if user.role == UserRole.STUDENT and not subject.graph_approved:
        raise ForbiddenError("The teacher has not approved this subject's concepts yet.")
    return [concept_service.serialize(c, db=db, user=user) for c in concept_service.list_concepts(db, subject_id)]


@router.get("/{concept_id}", response_model=ConceptOut, summary="Get a single concept with prerequisites and student mastery")
def get_concept_detail(concept_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    concept = concept_service.get_concept(db, concept_id)
    subject = subject_service.assert_can_view(db, user, concept.subject_id)
    if user.role == UserRole.STUDENT and not subject.graph_approved:
        raise ForbiddenError("The teacher has not approved this subject's concepts yet.")
    return concept_service.serialize(concept, db=db, user=user)



@router.put("/{concept_id}", response_model=ConceptOut, summary="Teacher: edit name/description/difficulty")
def update_concept(concept_id: int, data: ConceptUpdate, teacher: User = Depends(require_teacher),
                   db: Session = Depends(get_db)):
    concept = concept_service.get_concept(db, concept_id)
    subject_service.assert_teacher_owns(db, teacher, concept.subject_id)
    return concept_service.serialize(concept_service.update_concept(db, concept, data))


@router.delete("/{concept_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Teacher: delete a concept")
def delete_concept(concept_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    concept = concept_service.get_concept(db, concept_id)
    subject_service.assert_teacher_owns(db, teacher, concept.subject_id)
    concept_service.delete_concept(db, concept)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{concept_id}/prerequisites", response_model=ConceptOut, status_code=status.HTTP_201_CREATED,
             summary="Teacher: add a prerequisite (rejects duplicates and circular dependencies)")
def add_prerequisite(concept_id: int, data: PrerequisiteCreate, teacher: User = Depends(require_teacher),
                     db: Session = Depends(get_db)):
    concept = concept_service.get_concept(db, concept_id)
    subject_service.assert_teacher_owns(db, teacher, concept.subject_id)
    concept_service.add_prerequisite(db, concept, data.prerequisite_id)
    db.refresh(concept)
    return concept_service.serialize(concept)


@router.delete("/{concept_id}/prerequisites/{prerequisite_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Teacher: remove a prerequisite")
def remove_prerequisite(concept_id: int, prerequisite_id: int, teacher: User = Depends(require_teacher),
                        db: Session = Depends(get_db)):
    concept = concept_service.get_concept(db, concept_id)
    subject_service.assert_teacher_owns(db, teacher, concept.subject_id)
    concept_service.remove_prerequisite(db, concept, prerequisite_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
