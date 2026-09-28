# Learning Debt Detection System: Frontend

React + Vite + Tailwind client for the FastAPI backend.

## Run
```bash
npm install
cp .env.example .env     # set VITE_API_BASE_URL (default http://localhost:8000/api)
npm run dev              # http://localhost:5173
```
Backend CORS must allow `http://localhost:5173`.

## Where things live
- `src/api/endpoints.js`: every backend path. Change paths here only.
- `src/api/adapters.js`: every assumption about response shapes. If a screen shows blanks or zeros, fix the mapper here.
- `src/api/*Api.js`: one module per backend area; all calls go through `client.js` (JWT header, 401 handling, error messages).
- `tailwind.config.js`: all design tokens (colors, font, radius, shadow). Replace these with your own UI design system values.
- `src/context/AuthContext.jsx`, `src/routes/guards.jsx`: auth state, `ProtectedRoute`, `RoleProtectedRoute`.

## Verify against http://localhost:8000/docs
Paths not in your spec are marked `ASSUMED` in `endpoints.js`:
- `GET /concepts/{id}`, `POST /concepts` (add concept), `GET /syllabus/{id}` (status polling)
- `GET /students/me/learning-debt/{subject_id}`
- `GET /students/me/dashboard`, `GET /teachers/me/dashboard`

Other assumptions: login sends JSON `{email, password, role}` (set `VITE_LOGIN_FORMAT=form` for OAuth2 form login); mastery values 0-1 or 0-100 are both handled; assessment submit sends `{answers:[{question_id, selected_option}]}`.

## Behavior notes
- No mock data. Failed calls show an error state with a retry button.
- Syllabus processing stages are shown only if the backend returns a `status`/`processing_status`; otherwise a neutral "processing" message is shown.
- The JWT is kept in `localStorage`. The backend remains the authority for permissions.
- Profile pages are read-only because no update endpoint is defined.
