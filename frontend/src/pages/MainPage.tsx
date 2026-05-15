import HeaderMainPage from '../components/HeaderMainPage';
import StartNewProject from '../components/StartNewProject';
import RecentProjects from '../components/RecentProjects';
import { useRecentProjects } from '../hooks/useRecentProjects';
import ErrorMessage from '../components/common/ErrorMessage';

export default function MainPage() {
  const { projects, loading, error } = useRecentProjects();

  return (
    <div className="min-h-screen text-opacity-100 p-8" style={{ backgroundColor: 'var(--color-background)', color: 'var(--color-text-primary)' }}>
      <HeaderMainPage />
      <StartNewProject />
      <RecentProjects projects={projects} />

      {loading && (
        <p className="mt-6 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          Loading recent projects...
        </p>
      )}

      {!loading && !error && projects.length === 0 && (
        <ErrorMessage message="No recent projects found. Check that your Supabase table has rows in the projects table and that raw_json contains valid data." centered={false} />
      )}

      {error && (
        <ErrorMessage message={`Failed to load recent projects: ${error}`} centered={false} />
      )}
    </div>
  );
}