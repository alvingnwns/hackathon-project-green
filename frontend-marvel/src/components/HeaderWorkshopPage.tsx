import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

export default function HeaderWorkshopPage() {
  return (
    <header className="flex items-center justify-between px-4 py-2">
      <Link
        to="/"
        className="flex items-center gap-2 text-sm font-medium rounded-md px-2 py-2 border transition outline-none cursor-pointer"
        style={{
            backgroundColor: 'var(--color-surface)',
            color: 'var(--color-text-primary)',
            borderColor: 'var(--color-border)',
        }}

        onMouseEnter={(e) => {
          e.currentTarget.style.color = 'var(--color-brand-green)';
          e.currentTarget.style.borderColor = 'var(--color-brand-green)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = 'var(--color-text-primary)';
          e.currentTarget.style.borderColor = 'var(--color-border)';
        }}
    >
        <Home size={24} />
    </Link>

      <h1 className="text-2xl font-bold pr-4" style={{ color: 'var(--color-brand-green)' }}>
        GreenScape AI
      </h1>
    </header>
  );
}
