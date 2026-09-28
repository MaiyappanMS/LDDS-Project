"""Optional DEMO data: 'Programming Fundamentals' with concepts, prerequisites and sample questions.
The real application works with any teacher-uploaded syllabus; this is only a shortcut for demos/tests.
Run:  python -m scripts.seed_demo
Logins:  teacher@demo.edu / student@demo.edu   password: Password123!
"""
from sqlalchemy import select

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models import College, Concept, ConceptDependency, Question, Subject, SubjectEnrollment, User
from app.models.enums import Difficulty, QuestionType, UserRole

PASSWORD = "Password123!"
C, A, S, E = QuestionType.CONCEPTUAL, QuestionType.APPLICATION, QuestionType.SCENARIO, QuestionType.ERROR_SPOTTING
B, I = Difficulty.BEGINNER, Difficulty.INTERMEDIATE

CONCEPTS = [  # name, description, difficulty, prerequisites
    ("Variables", "Named storage locations that hold values.", B, []),
    ("Data Types", "Kinds of values such as integers, floats, strings and booleans.", B, ["Variables"]),
    ("Operators", "Symbols that perform arithmetic, comparison and logical operations.", B, ["Data Types"]),
    ("Conditional Statements", "Code that runs only when a condition is true.", I, ["Operators"]),
    ("Loops", "Repeating a block of code while a condition holds or over a sequence.", I, ["Conditional Statements"]),
    ("Functions", "Reusable named blocks of code with parameters and return values.", I,
     ["Conditional Statements", "Loops"]),
    ("Arrays", "Ordered collections of values accessed by index.", I, ["Data Types", "Loops"]),
]

QUESTIONS = {  # concept -> [(text, options, correct index, explanation, type)]
    "Variables": [
        ("What does the statement `count = 5` do?",
         ["Compares count with 5", "Stores the value 5 in a variable named count", "Prints 5", "Creates a constant"], 1,
         "Assignment stores a value under a name.", C),
        ("After `x = 3` and then `x = x + 2`, what is x?", ["3", "2", "5", "Error"], 2,
         "The right side is evaluated first (3 + 2) and stored back into x.", A),
        ("Which is a valid Python variable name?", ["2nd_score", "total-marks", "total_marks", "class"], 2,
         "Names cannot start with a digit, contain '-', or be keywords.", E),
    ],
    "Data Types": [
        ("Which type best stores the value 3.14?", ["int", "float", "str", "bool"], 1,
         "Numbers with a decimal part are floats.", C),
        ("What is the result of '5' + '3' in Python?", ["8", "'53'", "8.0", "TypeError"], 1,
         "Adding two strings concatenates them.", A),
        ("A program stores age as the string '18' and evaluates age + 1. What happens?",
         ["19", "'181'", "TypeError", "0"], 2, "Strings and integers cannot be added without conversion.", S),
    ],
    "Operators": [
        ("What is the value of 7 // 2?", ["3.5", "3", "4", "1"], 1, "// is floor division.", A),
        ("Which operator tests equality?", ["=", "==", "!=", "=>"], 1, "= assigns, == compares.", C),
        ("What is 2 + 3 * 4?", ["20", "14", "24", "9"], 1, "Multiplication has higher precedence.", A),
    ],
    "Conditional Statements": [
        ("When does the else block of an if/else run?", ["When the if condition is true",
                                                          "When the if condition is false", "Always", "Never"], 1,
         "else runs only if the if condition is false.", C),
        ("For x = 10: `if x > 5: print('A')` `elif x > 8: print('B')` prints what?", ["A", "B", "A and B", "nothing"],
         0, "Only the first true branch runs.", A),
        ("Which condition checks that n is between 1 and 10 inclusive?",
         ["1 <= n <= 10", "n >= 1 or n <= 10", "n > 1 and n < 10", "n = 1 to 10"], 0,
         "Both bounds must hold and be inclusive.", E),
    ],
    "Loops": [
        ("How many times does `for i in range(3):` run its body?", ["2", "3", "4", "infinite"], 1,
         "range(3) yields 0, 1, 2.", C),
        ("What most commonly causes an infinite while loop?",
         ["The condition never becomes false", "Using range", "Using print", "Indentation"], 0,
         "Nothing changes the loop condition.", S),
        ("What is total after: total = 0; for i in range(1, 4): total += i", ["3", "6", "10", "4"], 1,
         "1 + 2 + 3 = 6.", A),
    ],
    "Functions": [
        ("What is the main purpose of a function?",
         ["Make code slower", "Group reusable code under a name", "Store text", "Declare variables only"], 1,
         "Functions let you reuse logic.", C),
        ("What does add(2, 3) return for `def add(a, b): return a + b`?", ["23", "5", "None", "Error"], 1,
         "It returns the sum.", A),
        ("A function has no return statement. What does calling it evaluate to?", ["0", "None", "''", "Error"], 1,
         "Python returns None implicitly.", C),
    ],
    "Arrays": [
        ("In `nums = [10, 20, 30]`, what is nums[0]?", ["20", "10", "30", "IndexError"], 1,
         "Indexing starts at 0.", A),
        ("What is the index of the last element of a list with 5 items?", ["5", "4", "6", "1"], 1,
         "Indices run from 0 to 4.", C),
        ("What is len([4, 8, 15])?", ["2", "3", "15", "4"], 1, "It counts elements.", A),
    ],
}


def main() -> None:
    with SessionLocal() as db:
        college = db.scalar(select(College).where(College.name == "Demo College"))
        if not college:
            college = College(name="Demo College")
            db.add(college)
            db.flush()
        teacher = db.scalar(select(User).where(User.email == "teacher@demo.edu"))
        if not teacher:
            teacher = User(email="teacher@demo.edu", full_name="Demo Teacher", role=UserRole.TEACHER,
                           hashed_password=hash_password(PASSWORD), college_id=college.id)
            db.add(teacher)
        student = db.scalar(select(User).where(User.email == "student@demo.edu"))
        if not student:
            student = User(email="student@demo.edu", full_name="Demo Student", role=UserRole.STUDENT,
                           hashed_password=hash_password(PASSWORD), college_id=college.id)
            db.add(student)
        db.flush()

        if db.scalar(select(Subject).where(Subject.name == "Programming Fundamentals",
                                           Subject.college_id == college.id)):
            print("Demo subject already exists; nothing to do.")
            db.commit()
            return
        subject = Subject(college_id=college.id, name="Programming Fundamentals", semester="1",
                          description="Demo subject", created_by=teacher.id, graph_approved=True)
        db.add(subject)
        db.flush()
        by_name: dict[str, Concept] = {}
        for pos, (name, desc, diff, _) in enumerate(CONCEPTS, start=1):
            by_name[name] = Concept(subject_id=subject.id, name=name, description=desc, difficulty=diff, position=pos)
            db.add(by_name[name])
        db.flush()
        for name, _, _, prereqs in CONCEPTS:
            for p in prereqs:
                db.add(ConceptDependency(concept_id=by_name[name].id, prerequisite_id=by_name[p].id))
        for cname, items in QUESTIONS.items():
            for text, options, idx, expl, qtype in items:
                db.add(Question(subject_id=subject.id, concept_id=by_name[cname].id, question_text=text,
                                question_type=qtype, options=options, correct_answer=options[idx], explanation=expl,
                                difficulty=by_name[cname].difficulty, is_ai_generated=False, created_by=teacher.id))
        db.add(SubjectEnrollment(subject_id=subject.id, student_id=student.id))
        db.commit()
        print(f"Seeded subject id={subject.id}. Logins: teacher@demo.edu / student@demo.edu, password {PASSWORD}")


if __name__ == "__main__":
    main()
