# Import every model so Base.metadata knows all tables (needed by Alembic and create_all).
from app.models.answer import StudentAnswer  # noqa: F401
from app.models.assessment import Assessment, AssessmentQuestion  # noqa: F401
from app.models.college import College  # noqa: F401
from app.models.concept import Concept, ConceptDependency  # noqa: F401
from app.models.learning_debt import LearningDebt  # noqa: F401
from app.models.mastery import ConceptMastery  # noqa: F401
from app.models.question import Question  # noqa: F401
from app.models.subject import Subject, SubjectEnrollment  # noqa: F401
from app.models.syllabus import Syllabus  # noqa: F401
from app.models.user import User  # noqa: F401
