import { Suspense } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Canvas } from '@react-three/fiber';
import { useProject } from '../hooks/useProject';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { Scene, SceneErrorBoundary } from '../components/workshop/Scene3D';
import WorkshopLeftBar from '../components/workshop/WorkshopLeftBar';
import WorkshopRightBar from '../components/workshop/WorkshopRightBar';
import BlankCanvasPlaceholder from '../components/workshop/BlankCanvasPlaceholder';
import ProjectNotFound from '../components/workshop/ProjectNotFound';
import HeaderWorkshopPage from '../components/HeaderWorkshopPage';

export default function WorkshopPage() {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('id');
  const { projectData, loading, error } = useProject(projectId);

  // Determine the current state
  const isBlankState = projectId === 'blank';
  const isErrorState = !isBlankState && !loading && error; // Only show error if there's actually an error

  // Loading state - show loading spinner in middle panel
  if (loading && !isBlankState) {
    return (
      <div className='h-screen w-full flex flex-col overflow-hidden'>
        <HeaderWorkshopPage />
        <div className="flex flex-1 min-h-0 overflow-hidden" style={{ backgroundColor: 'var(--color-background)' }}>
          <WorkshopLeftBar />
          <div className="flex-1 flex items-center justify-center">
            <LoadingSpinner />
          </div>
          <WorkshopRightBar isBlank={true} />
        </div>
      </div>
    );
  }

  // Error/Not Found state
  if (isErrorState) {
    return (
      <div className='h-screen w-full flex flex-col overflow-hidden'>
        <HeaderWorkshopPage />
        <div className="flex flex-1 min-h-0 overflow-hidden" style={{ backgroundColor: 'var(--color-background)' }}>
          <WorkshopLeftBar />
          <ProjectNotFound />
          <WorkshopRightBar isBlank={true} />
        </div>
      </div>
    );
  }

  // Extract data for project state
  const analysis = projectData?.raw_json?.project_context?.gemini_full_report?.analysis;
  const greenSolution = projectData?.raw_json?.project_context?.gemini_full_report?.green_solution;
  const assets = projectData?.raw_json?.assets || [];

  return (
    <div className='h-screen w-full flex flex-col overflow-hidden'>
      <HeaderWorkshopPage />
      <div className="flex flex-1 min-h-0 overflow-hidden" style={{ backgroundColor: 'var(--color-background)', color: 'var(--color-text-primary)' }}>
        <WorkshopLeftBar />

        {/* Middle Screen */}
        {isBlankState ? (
          <BlankCanvasPlaceholder />
        ) : (
          <div className="flex-1 bg-black">
            <Suspense fallback={<LoadingSpinner />}>
              <Canvas
                camera={{ position: [5, 5, 5], fov: 75 }}
                dpr={[1, 1.5]}
                gl={{ antialias: true, powerPreference: 'high-performance', preserveDrawingBuffer: true }}
                onCreated={({ gl }) => {
                  gl.domElement.addEventListener('webglcontextlost', (event) => {
                    event.preventDefault();
                  });
                }}
              >
                <SceneErrorBoundary>
                  <Scene assets={assets} />
                </SceneErrorBoundary>
              </Canvas>
            </Suspense>
          </div>
        )}

        <WorkshopRightBar
          analysis={analysis}
          greenSolution={greenSolution}
          projectConcept={projectData?.concept_name}
          projectCost={projectData?.estimated_cost}
          isBlank={isBlankState}
        />
      </div>
    </div>
  );
}