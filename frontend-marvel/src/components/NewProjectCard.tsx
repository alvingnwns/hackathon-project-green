import { Link } from 'react-router-dom';

interface NewProjectCardProps {
  title: string;
  to?: string;
//   thumbnail: string;
}

export default function NewProjectCard({ title, to = '/workshop' }: NewProjectCardProps) {
  return (
    <div className="flex gap-4">
        <Link
          to={to}
          className="flex flex-col items-center justify-center w-40 h-32 rounded-xl transition cursor-pointer"
          style={{
            backgroundColor: 'var(--color-background-secondary)',
            border: '2px solid var(--color-brand-green-light)',
            color: 'var(--color-brand-green)',
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.backgroundColor = 'var(--color-background-tertiary)')
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.backgroundColor = 'var(--color-background-secondary)')
          }
        >
          <span className="text-3xl mb-2" style={{ color: 'var(--color-brand-green)' }}>
            +
          </span>
          <span className="text-sm font-medium" style={{ color: 'var(--color-brand-green)' }}>
            {title}
          </span>
        </Link>
      </div>
  )
}