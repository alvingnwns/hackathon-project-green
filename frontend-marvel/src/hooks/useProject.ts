import { useEffect, useState } from 'react';
import { supabase } from '../supabase';

export function useProject(projectId: string | null) {
  const [projectData, setProjectData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId || projectId === 'blank') {
      setLoading(false);
      setError(null);
      setProjectData(null);
      return;
    }

    const fetchProject = async () => {
      try {
        const { data, error } = await supabase
          .from('projects')
          .select('*')
          .eq('id', projectId)
          .single();

        if (error) throw error;

        setProjectData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch project');
      } finally {
        setLoading(false);
      }
    };

    fetchProject();
  }, [projectId]);

  return { projectData, loading, error };
}
