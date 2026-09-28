import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute, RoleProtectedRoute } from './routes/guards';
import { useAuth, homeFor } from './context/AuthContext';
import AppShell from './components/layout/AppShell';
import { PageSkeleton } from './components/ui/Skeleton';

const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const NotFound = lazy(() => import('./pages/NotFound'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));

const TeacherDashboard = lazy(() => import('./pages/teacher/Dashboard'));
const Subjects = lazy(() => import('./pages/teacher/Subjects'));
const SubjectDetail = lazy(() => import('./pages/teacher/SubjectDetail'));
const SyllabusUpload = lazy(() => import('./pages/teacher/SyllabusUpload'));
const ConceptReview = lazy(() => import('./pages/teacher/ConceptReview'));
const KnowledgeGraph = lazy(() => import('./pages/teacher/KnowledgeGraph'));
const Questions = lazy(() => import('./pages/teacher/Questions'));

const StudentDashboard = lazy(() => import('./pages/student/Dashboard'));
const StudentSubjectPage = lazy(() => import('./pages/student/SubjectPage'));
const Assessment = lazy(() => import('./pages/student/Assessment'));
const AssessmentResultPage = lazy(() => import('./pages/student/AssessmentResult'));
const LearningDebtPage = lazy(() => import('./pages/student/LearningDebt'));
const LearningPathPage = lazy(() => import('./pages/student/LearningPathPage'));
const ConceptDetail = lazy(() => import('./pages/student/ConceptDetail'));

function Home() {
  const { isAuthenticated, role, loading } = useAuth();
  if (loading) return <div className="p-8"><PageSkeleton /></div>;
  return <Navigate to={isAuthenticated ? homeFor(role) : '/login'} replace />;
}

export default function App() {
  return (
    <Suspense fallback={<div className="p-8"><PageSkeleton /></div>}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<RoleProtectedRoute role="TEACHER" />}>
            <Route element={<AppShell />}>
              <Route path="/teacher/dashboard" element={<TeacherDashboard />} />
              <Route path="/teacher/subjects" element={<Subjects />} />
              <Route path="/teacher/subjects/:id" element={<SubjectDetail />} />
              <Route path="/teacher/subjects/:id/syllabus" element={<SyllabusUpload />} />
              <Route path="/teacher/subjects/:id/concepts" element={<ConceptReview />} />
              <Route path="/teacher/subjects/:id/knowledge-graph" element={<KnowledgeGraph />} />
              <Route path="/teacher/subjects/:id/questions" element={<Questions />} />
              <Route path="/teacher/profile" element={<ProfilePage role="TEACHER" />} />
            </Route>
          </Route>

          <Route element={<RoleProtectedRoute role="STUDENT" />}>
            <Route element={<AppShell />}>
              <Route path="/student/dashboard" element={<StudentDashboard />} />
              <Route path="/student/subjects/:id" element={<StudentSubjectPage />} />
              <Route path="/student/assessment/:id" element={<Assessment />} />
              <Route path="/student/assessment/:id/result" element={<AssessmentResultPage />} />
              <Route path="/student/learning-debt/:id" element={<LearningDebtPage />} />
              <Route path="/student/learning-path/:id" element={<LearningPathPage />} />
              <Route path="/student/concepts/:id" element={<ConceptDetail />} />
              <Route path="/student/profile" element={<ProfilePage role="STUDENT" />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
