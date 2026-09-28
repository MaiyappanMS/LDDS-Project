# Learning Debt Detection System — Backend (MVP)

FastAPI + PostgreSQL (NeonDB) + SQLAlchemy 2 + Alembic + JWT. Teachers upload **any** syllabus; an LLM proposes a
concept graph; the teacher reviews/approves it; students take assessments; **deterministic Python** computes concept
mastery, learning debt and a learning path; the LLM is only used to *explain* the results.

## 1. What "learning debt" means here
A concept is **weak** if mastery < 60 %. A weak concept is *learning debt* because every concept that (directly or
indirectly) depends on it is put at risk. For each weak concept the engine reports its mastery, severity, whether it is a
**root cause** (none of its prerequisites are weak), the **affected** downstream concepts, and a priority score.

```
Variables (30%) -> Data Types (40%) -> Operators (90%) -> Functions (35%)
=> Variables and Data Types are foundational debt; Functions is weak partly because of them.
```

## 2. Architecture
```
React  ->  FastAPI routes  ->  JWT auth / role checks  ->  services  ->  PostgreSQL (NeonDB)
                                                              \-> ai_service (LLM, JSON-validated, cached)
```
| Layer | Files |
|---|---|
| Routes (thin) | `app/routes/*.py` |
| Business logic | `app/services/*.py` |
| Pure logic (no DB/AI, unit-tested) | `services/graph_utils.py`, `services/debt_engine.py` |
| Models / schemas | `app/models/*.py`, `app/schemas/*.py` |
| Config / security | `app/core/*.py` |

Note: the spec listed `subject_service` implicitly; extra files added: `subject_service.py`, `syllabus_service.py`,
`graph_utils.py`, `debt_engine.py`, `models/enums.py`, `core/exceptions.py`.

### How the pieces work
* **Syllabus**: PDF (PyMuPDF), DOCX (python-docx) or TXT is validated (type, size, empty, magic bytes) and parsed in
  memory (nothing is kept on disk). Image-only PDFs return a clear "OCR required" error.
* **AI analysis** returns JSON that is validated with Pydantic; one retry on invalid output, then a controlled 502.
  The validated result is cached in `syllabi.analysis_json`. Unknown prerequisite names are dropped and edges that would
  create a cycle are skipped, both reported as `warnings`. Concepts are saved **unapproved** for teacher review.
* **Knowledge graph**: `concept_dependencies` rows (`prerequisite -> concept`). Every insert is checked for
  self-reference, duplicates and cycles. Students can only be assessed after `POST /api/subjects/{id}/approve-graph`.
* **Mastery** (transparent heuristic, *not* scientifically validated): `correct / total * 100` over the student's latest
  `MASTERY_WINDOW` (10) answers per concept. `confidence = min(1, questions / 3)` so one lucky guess is visibly
  low-confidence. Bands (configurable): `<40 HIGH_DEBT`, `<60 MODERATE_DEBT`, `<80 DEVELOPING`, `>=80 MASTERED`.
* **Severity**: `high` if mastery < 40, otherwise `moderate`; a moderate concept blocking >= 3 concepts is escalated to
  `high`. `priority_score = (100 - mastery) * (1 + number_of_affected_concepts)`.
* **Learning path**: weak concepts plus their prerequisites that are not yet mastered, ordered by a topological sort of the
  graph (prerequisites always first); ties broken by "blocks the most weak concepts", then lowest mastery.
* **AI explanations** are on demand (`POST .../explain`), limited to the top 3 debts, cached per debt and only regenerated
  if the underlying numbers change. The AI never changes scores; an AI-suggested order that mentions unknown concepts is
  replaced by the graph-derived order.

## 3. Requirements
Python 3.12+, a NeonDB (PostgreSQL) database, an LLM API key (Anthropic, or any OpenAI-compatible provider).

## 4. Setup (Windows PowerShell)
```powershell
cd learning-debt-backend
python -m venv venv
.\venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
Copy-Item .env.example .env          # then edit .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # paste into JWT_SECRET_KEY
```
macOS/Linux: `python3 -m venv venv && source venv/bin/activate`.

## 5. Environment variables (`.env`)
| Variable | Meaning |
|---|---|
| `DATABASE_URL` | NeonDB connection string. `postgresql://` is auto-converted to `postgresql+psycopg://` |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT settings |
| `AI_PROVIDER` | `anthropic` (default) or `openai` (any OpenAI-compatible API) |
| `AI_API_KEY`, `AI_MODEL`, `AI_BASE_URL` | Provider credentials/model. `AI_BASE_URL` only for OpenAI-compatible providers |
| `FRONTEND_URL` | Allowed CORS origin(s), comma-separated (e.g. `http://localhost:5173`) |
| `MAX_UPLOAD_SIZE_MB` | Upload limit (default 10) |
| `THRESHOLD_*`, `MASTERY_WINDOW`, `MIN_QUESTIONS_FOR_FULL_CONFIDENCE` | Optional scoring overrides |

## 6. NeonDB setup
1. Create a project at https://neon.tech and open **Connection Details**.
2. Copy the connection string (it already contains `sslmode=require`) into `DATABASE_URL` in `.env`.
3. Use the *direct* connection for migrations if the pooled one gives trouble.
4. For tests create a **separate Neon branch/database** whose name contains `test`.

## 7. Migrations (Alembic)
```powershell
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```
Quick demo fallback without migration history: `python -m scripts.create_tables`.
Optional demo data: `python -m scripts.seed_demo` (logins `teacher@demo.edu` / `student@demo.edu`, password `Password123!`).

## 8. Run
```powershell
python -m uvicorn app.main:app --reload
```
Swagger: http://127.0.0.1:8000/docs · ReDoc: http://127.0.0.1:8000/redoc · Health: `/health`.
In Swagger click **Authorize** and log in with your email as the username.

## 9. Demo flow (any syllabus, nothing hardcoded)
```powershell
$B = "http://127.0.0.1:8000"
# Teacher
$t = Invoke-RestMethod "$B/api/auth/register" -Method Post -ContentType application/json -Body (@{email="t@uni.edu";password="Password123!";full_name="Dr T";role="TEACHER";college_name="My College"} | ConvertTo-Json)
$H = @{Authorization="Bearer $($t.access_token)"}
$s = Invoke-RestMethod "$B/api/subjects" -Method Post -Headers $H -ContentType application/json -Body (@{name="Programming Fundamentals";semester="1"} | ConvertTo-Json)
curl.exe -X POST "$B/api/syllabus/upload" -H "Authorization: Bearer $($t.access_token)" -F "subject_id=$($s.id)" -F "file=@sample_data/programming_fundamentals_syllabus.txt"
Invoke-RestMethod "$B/api/concepts/subject/$($s.id)" -Headers $H                       # review
Invoke-RestMethod "$B/api/subjects/$($s.id)/approve-graph" -Method Post -Headers $H    # approve
# generate questions per concept (repeat for each concept id)
Invoke-RestMethod "$B/api/questions/generate" -Method Post -Headers $H -ContentType application/json -Body (@{subject_id=$s.id;concept_id=1;number_of_questions=3} | ConvertTo-Json)
```
Student: register with `college_id` → `POST /api/subjects/{id}/enroll` → `POST /api/assessments` →
`GET /api/assessments/{id}/questions` → `POST /api/assessments/{id}/submit` (`{"answers":[{"question_id":1,"selected_answer":"..."}]}`) →
`GET /api/students/me/dashboard/{subject_id}` and `POST /api/students/me/learning-debt/{subject_id}/explain`.

### Endpoint overview
| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/token` (Swagger form), `GET /api/auth/me` |
| Colleges / Users | `POST/GET /api/colleges`, `GET /api/colleges/{id}`, `GET /api/users/me`, `GET /api/users/students?subject_id=` |
| Subjects | `POST/GET /api/subjects`, `GET /api/subjects/available`, `GET /api/subjects/{id}`, `POST /api/subjects/{id}/enroll`, `GET /api/subjects/{id}/knowledge-graph`, `POST /api/subjects/{id}/approve-graph` |
| Syllabus | `POST /api/syllabus/upload`, `POST /api/syllabus/{id}/analyze?force=`, `GET /api/syllabus/subject/{id}` |
| Concepts | `POST /api/concepts`, `GET /api/concepts/subject/{id}`, `PUT/DELETE /api/concepts/{id}`, `POST /api/concepts/{id}/prerequisites`, `DELETE /api/concepts/{id}/prerequisites/{pid}` |
| Questions | `POST /api/questions/generate`, `GET /api/questions/concept/{id}`, `DELETE /api/questions/{id}` |
| Assessments | `POST /api/assessments`, `GET /api/assessments/{id}`, `GET .../questions`, `POST .../submit`, `GET /api/assessments/subject/{id}/results` (teacher) |
| Student | `GET /api/students/me/{mastery,learning-debt,learning-path,dashboard}/{subject_id}`, `POST /api/students/me/learning-debt/{subject_id}/explain` |
| Teacher | `GET /api/teachers/me/dashboard/{subject_id}`, `GET /api/teachers/me/students/{sid}/learning-debt/{subject_id}` |

Errors always look like `{"error": {"code": "...", "message": "..."}}` (validation errors keep FastAPI's default 422 format).

## 10. Frontend connection (React/Vite)
Set `FRONTEND_URL=http://localhost:5173`. In React:
```js
const api = axios.create({ baseURL: "http://127.0.0.1:8000" });
api.interceptors.request.use(c => { c.headers.Authorization = `Bearer ${localStorage.getItem("token")}`; return c; });
```
The knowledge graph endpoint returns `{nodes:[{id,name,...}], edges:[{source,target}]}` (source = prerequisite),
ready for React Flow / vis-network.

## 11. Tests
```powershell
python -m pytest tests/test_debt_engine.py            # pure logic: mastery, debt, path, cycles (no DB / AI)
python -m pytest tests/test_syllabus_parser.py        # TXT/DOCX/PDF extraction + error cases
$env:TEST_DATABASE_URL = "postgresql+psycopg://...test-branch..."   # DISPOSABLE DB, name must contain 'test'
python -m pytest                                      # + full API flow with a fake AI (drops/recreates tables!)
```

## 12. Troubleshooting
| Problem | Fix |
|---|---|
| `ValidationError: database_url / jwt_secret_key field required` | `.env` missing or not in the working directory |
| `SSL connection` / `connection refused` | Keep `?sslmode=require`; check the Neon project isn't suspended (first request may take a few seconds) |
| `relation "users" does not exist` | Run `alembic upgrade head` (or `python -m scripts.create_tables`) |
| `AI is not configured` / 502 `ai_service_error` | Set `AI_API_KEY`, `AI_MODEL` (and `AI_PROVIDER`/`AI_BASE_URL`); check server logs for the provider status |
| PDF: "No extractable text ... OCR" | The PDF is a scan; upload a text PDF, DOCX or TXT |
| CORS error in browser | `FRONTEND_URL` must exactly match the origin (scheme + host + port) |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Password rejected | 8–72 bytes |

## 13. Known limitations (MVP)
* Syllabus analysis runs synchronously inside the upload request (typically 10–60 s); large syllabi are truncated to
  `AI_MAX_INPUT_CHARS` (30 000 chars).
* No OCR. Mastery is a simple heuristic; it is not a validated psychometric model (no IRT, no guess-correction).
* Editing/deleting concepts after students were assessed does not retroactively recompute their mastery until they
  submit a new assessment.
* No refresh tokens / password reset / rate limiting.
