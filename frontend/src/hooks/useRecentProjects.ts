import { useEffect, useState } from 'react';
import { supabase } from '../supabase';
import { formatProjectDate } from '../utils/dateFormat';

export interface ProjectItem {
  id: string;
  title: string;
  date: string;
  thumbnail: string;
}

const DEFAULT_THUMBNAIL = 'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=400&q=80';

export function useRecentProjects() {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      setError(null);

      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(12);

      if (error) {
        setError(error.message);
        setProjects([]);
        setLoading(false);
        return;
      }

      const mappedProjects = (data ?? []).map((project: any) => {
        const rawJson = project.raw_json ?? {};
        const title =
          project.concept_name ||
          rawJson.project_context?.gemini_full_report?.green_solution?.concept_name ||
          'Untitled project';
        const date = formatProjectDate(project.created_at);
        const thumbnail = rawJson.assets?.[0]?.thumbnail_url || DEFAULT_THUMBNAIL;

        return {
          id: project.id,
          title,
          date,
          thumbnail,
        };
      });

      setProjects(mappedProjects);
      setLoading(false);
    };

    fetchProjects();
  }, []);

  return { projects, loading, error };
}
