"""End-to-end API tests. The AI is replaced by deterministic fakes, so no external API is needed."""
import uuid

from app.services import ai_service


def _email(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def register(client, role, college_name=None, college_id=None):
    body = {"email": _email(role.lower()), "password": "Sup3rSecret!", "full_name": role.title(), "role": role}
    if college_name:
        body["college_name"] = college_name
    if college_id:
        body["college_id"] = college_id
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 201, r.text
    data = r.json()
    return {"Authorization": f"Bearer {data['access_token']}"}, data["user"], body


def fake_analysis(subject_name, text):
    D = ai_service.ConceptDraft
    return ai_service.SyllabusAnalysis(concepts=[
        D(name="Variables", description="Named storage", difficulty="beginner", prerequisites=[]),
        D(name="Data Types", description="Kinds of values", difficulty="beginner", prerequisites=["Variables"]),
        D(name="Functions", description="Reusable code", difficulty="intermediate",
          prerequisites=["Data Types", "Variables", "Unknown Thing"]),
    ])


def fake_questions(subject_name, concept_name, concept_description, difficulty, count, prerequisite_names):
    return [ai_service.QuestionDraft(
        question_text=f"Question {i} about {concept_name}?", options=["A", "B", "C", "D"], correct_answer="B",
        explanation="B is right", difficulty=difficulty.value.lower(), question_type="CONCEPTUAL")
        for i in range(count)]


def test_auth_register_login_me_and_bad_token(client):
    headers, user, body = register(client, "TEACHER", college_name="Auth College")
    assert "hashed_password" not in user
    assert client.post("/api/auth/register", json=body).status_code == 409  # duplicate email
    r = client.post("/api/auth/login", json={"email": body["email"], "password": body["password"]})
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"
    assert client.post("/api/auth/login", json={"email": body["email"], "password": "wrong-password"}).status_code == 401
    assert client.get("/api/auth/me", headers=headers).json()["email"] == body["email"].lower()
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401
    assert client.get("/api/auth/me").status_code == 401


def test_full_learning_debt_flow(client, monkeypatch):
    monkeypatch.setattr(ai_service, "analyze_syllabus", fake_analysis)
    monkeypatch.setattr(ai_service, "generate_questions", fake_questions)

    # ---- teacher: subject + syllabus upload
    t_headers, teacher, _ = register(client, "TEACHER", college_name=f"Flow College {uuid.uuid4().hex[:6]}")
    r = client.post("/api/subjects", json={"name": "Programming Fundamentals", "semester": "1"}, headers=t_headers)
    assert r.status_code == 201, r.text
    subject_id, college_id = r.json()["id"], r.json()["college_id"]

    syllabus = ("Unit 1 Variables and data types. Unit 2 Functions and reusable code blocks. " * 2).encode()
    r = client.post("/api/syllabus/upload", headers=t_headers, data={"subject_id": subject_id},
                    files={"file": ("syllabus.txt", syllabus, "text/plain")})
    assert r.status_code == 201, r.text
    assert r.json()["concepts_created"] == 3 and r.json()["dependencies_created"] == 3
    assert any("Unknown Thing" in w for w in r.json()["warnings"])  # unknown prerequisite ignored, not saved

    concepts = client.get(f"/api/concepts/subject/{subject_id}", headers=t_headers).json()
    ids = {c["name"]: c["id"] for c in concepts}
    graph = client.get(f"/api/subjects/{subject_id}/knowledge-graph", headers=t_headers).json()
    assert len(graph["nodes"]) == 3
    assert {"source": ids["Variables"], "target": ids["Data Types"]} in graph["edges"]

    # ---- concept review: cycle + duplicate protection, manual edits
    r = client.post(f"/api/concepts/{ids['Variables']}/prerequisites", json={"prerequisite_id": ids["Functions"]},
                    headers=t_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "circular_dependency"
    r = client.post(f"/api/concepts/{ids['Data Types']}/prerequisites", json={"prerequisite_id": ids["Variables"]},
                    headers=t_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "duplicate_relationship"
    r = client.put(f"/api/concepts/{ids['Variables']}", json={"description": "Edited"}, headers=t_headers)
    assert r.status_code == 200 and r.json()["description"] == "Edited"
    r = client.post("/api/concepts", headers=t_headers,
                    json={"subject_id": subject_id, "name": "Arrays", "prerequisite_ids": [ids["Data Types"]]})
    assert r.status_code == 201
    client.delete(f"/api/concepts/{r.json()['id']}", headers=t_headers)

    # ---- students cannot be assessed before approval; then approve + generate questions
    s_headers, student, _ = register(client, "STUDENT", college_id=college_id)
    assert client.post(f"/api/subjects/{subject_id}/enroll", headers=s_headers).status_code == 200
    assert client.post("/api/assessments", json={"subject_id": subject_id}, headers=s_headers).status_code == 409
    assert client.post(f"/api/subjects/{subject_id}/approve-graph", headers=t_headers).status_code == 200
    for name, cid in ids.items():
        r = client.post("/api/questions/generate", headers=t_headers,
                        json={"subject_id": subject_id, "concept_id": cid, "number_of_questions": 3})
        assert r.status_code == 201 and len(r.json()) == 3

    # ---- student: assessment; correct answers are hidden
    r = client.post("/api/assessments", json={"subject_id": subject_id}, headers=s_headers)
    assert r.status_code == 201
    aid = r.json()["id"]
    questions = client.get(f"/api/assessments/{aid}/questions", headers=s_headers).json()
    assert len(questions) == 9 and all("correct_answer" not in q for q in questions)

    # incomplete submission rejected
    r = client.post(f"/api/assessments/{aid}/submit", headers=s_headers,
                    json={"answers": [{"question_id": questions[0]["id"], "selected_answer": "A"}]})
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_submission"

    # fail Variables + Functions, pass Data Types
    answers = [{"question_id": q["id"], "selected_answer": "B" if q["concept_name"] == "Data Types" else "A"}
               for q in questions]
    r = client.post(f"/api/assessments/{aid}/submit", json={"answers": answers}, headers=s_headers)
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["assessment"]["score"] == 33.3 and result["assessment"]["status"] == "COMPLETED"
    mastery = {m["concept"]: m["mastery_percentage"] for m in result["mastery"]}
    assert mastery == {"Variables": 0.0, "Data Types": 100.0, "Functions": 0.0}
    debts = {d["concept"]: d for d in result["learning_debt"]}
    assert debts["Variables"]["is_root_cause"] and debts["Variables"]["severity"] == "high"
    assert debts["Variables"]["affected_concepts"] == ["Data Types", "Functions"]
    assert debts["Functions"]["caused_by"] == ["Variables"]
    assert client.post(f"/api/assessments/{aid}/submit", json={"answers": answers}, headers=s_headers).status_code == 409

    # ---- learning path + dashboards
    path = client.get(f"/api/students/me/learning-path/{subject_id}", headers=s_headers).json()["steps"]
    assert [s["concept"] for s in path] == ["Variables", "Functions"]
    dash = client.get(f"/api/students/me/dashboard/{subject_id}", headers=s_headers).json()
    assert dash["learning_debt_count"] == 2 and len(dash["assessment_history"]) == 1
    tdash = client.get(f"/api/teachers/me/dashboard/{subject_id}", headers=t_headers).json()
    assert tdash["enrolled_students"] == 1 and tdash["assessment_stats"]["completed_assessments"] == 1
    assert tdash["learning_debt_stats"]["most_common_root_causes"][0]["concept"] == "Variables"

    # ---- access control
    assert client.get(f"/api/teachers/me/dashboard/{subject_id}", headers=s_headers).status_code == 403
    other_headers, _, _ = register(client, "TEACHER", college_name="Other College")
    assert client.get(f"/api/concepts/subject/{subject_id}", headers=other_headers).status_code == 403
    assert client.get(f"/api/assessments/{aid}", headers=other_headers).status_code == 403
    other_student, _, _ = register(client, "STUDENT", college_id=college_id)
    assert client.get(f"/api/assessments/{aid}/questions", headers=other_student).status_code == 403
    r = client.post("/api/questions/generate", headers=other_headers,
                    json={"subject_id": subject_id, "concept_id": ids["Variables"]})
    assert r.status_code == 403


def test_unsupported_and_empty_upload(client):
    t_headers, _, _ = register(client, "TEACHER", college_name=f"Upload College {uuid.uuid4().hex[:6]}")
    sid = client.post("/api/subjects", json={"name": "Any Subject"}, headers=t_headers).json()["id"]
    r = client.post("/api/syllabus/upload", headers=t_headers, data={"subject_id": sid},
                    files={"file": ("virus.exe", b"MZ...", "application/octet-stream")})
    assert r.status_code == 415
    r = client.post("/api/syllabus/upload", headers=t_headers, data={"subject_id": sid},
                    files={"file": ("empty.txt", b"", "text/plain")})
    assert r.status_code == 400
