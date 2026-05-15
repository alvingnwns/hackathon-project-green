import { Link } from 'react-router-dom';
import { AlertCircle, Home } from 'lucide-react';

export default function ProjectNotFound() {
  return (
    <div className="flex-1 flex items-center justify-center" style={{ backgroundColor: 'var(--color-background)' }}>
      <div className="text-center space-y-6 max-w-md">
        <div className="flex justify-center">
          <AlertCircle size={64} style={{ color: 'var(--color-text-secondary)' }} />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            Project not found
          </h2>
          <p className="text-base" style={{ color: 'var(--color-text-secondary)' }}>
            The project you're looking for doesn't exist in the database or may have been deleted.
          </p>
        </div>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-md font-medium transition"
          style={{
            backgroundColor: 'var(--color-brand-green)',
            color: 'var(--color-text-inverse)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-brand-green-dark)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-brand-green)';
          }}
        >
          <Home size={20} />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}