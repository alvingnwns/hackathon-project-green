import { Link } from 'react-router-dom';

interface ProjectCardProps {
  id: string;
  title: string;
  date: string;
  thumbnail: string;
}

export default function ProjectCard({ id, title, date, thumbnail }: ProjectCardProps) {
  return (
    <Link to={`/workshop?id=${id}`} className="group block cursor-pointer">
      {/* Thumbnail */}
      <div
        className="w-full aspect-video rounded-xl overflow-hidden mb-3 border-2 transition"
        style={{
          backgroundColor: 'var(--color-background-secondary)',
          borderColor: 'var(--color-border)',
        }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.borderColor = 'var(--color-brand-green)')
        }
        onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--color-border)')}
      >
        <img
          src={thumbnail}
          alt={title}
          className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
        />
      </div>
      {/* Metadata */}
      <h3
        className="font-medium transition"
        style={{ color: 'var(--color-text-primary)' }}
        onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-brand-green)')}
        onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-primary)')}
      >
        {title}
      </h3>
      <p className="text-xs" style={{ color: 'var(--color-text-light)' }}>
        {date}
      </p>
    </Link>
  );
}
