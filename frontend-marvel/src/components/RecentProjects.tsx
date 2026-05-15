import ProjectCard from './ProjectCard';
import { useState } from 'react';
import { Search } from 'lucide-react';

interface Project {
  id: string;
  title: string;
  date: string;
  thumbnail: string;
}

interface RecentProjectsProps {
  projects: Project[];
}

export default function RecentProjects({ projects }: RecentProjectsProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredProjects = projects.filter((project) =>
    project.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold" style={{ color: 'var(--color-brand-green)' }}>
          Recent designs
        </h2>
        {/* Search Placeholder */}
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" size={16} />
          <input 
            type="text"
            placeholder="Search projects..."
            value={searchQuery} // Bind ke state
            onChange={(e) => setSearchQuery(e.target.value)} // Update state saat mengetik
            className="text-sm rounded-md pl-8 py-2 w-64 focus:outline-none transition"
            style={{
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-text-primary)',
              border: '1px solid var(--color-border)',
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--color-brand-green)')}
            onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--color-border)')}
          />
        </div>
      </div>

      {/* Canva-style Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {filteredProjects.map((project) => (
          <ProjectCard
            key={project.id}
            id={project.id}
            title={project.title}
            date={project.date}
            thumbnail={project.thumbnail}
          />
        ))}

        {filteredProjects.length === 0 && (
          <p className="text-neutral-500 mt-10 text-left">No projects found for "{searchQuery}"</p>
        )}
      </div>
    </section>
  );
}
