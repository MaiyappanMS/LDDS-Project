import { LayoutDashboard, BookOpen, User } from 'lucide-react';
export const NAV = {
  TEACHER: [
    { to: '/teacher/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/teacher/subjects', label: 'Subjects', icon: BookOpen },
    { to: '/teacher/profile', label: 'Profile', icon: User },
  ],
  STUDENT: [
    { to: '/student/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/student/profile', label: 'Profile', icon: User },
  ],
};
