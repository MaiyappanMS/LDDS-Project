import enum


class UserRole(str, enum.Enum):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class Difficulty(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class QuestionType(str, enum.Enum):
    CONCEPTUAL = "CONCEPTUAL"
    APPLICATION = "APPLICATION"
    SCENARIO = "SCENARIO"
    TRUE_FALSE = "TRUE_FALSE"
    ERROR_SPOTTING = "ERROR_SPOTTING"


class SyllabusStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


class AssessmentStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class MasteryStatus(str, enum.Enum):
    HIGH_DEBT = "HIGH_DEBT"
    MODERATE_DEBT = "MODERATE_DEBT"
    DEVELOPING = "DEVELOPING"
    MASTERED = "MASTERED"
