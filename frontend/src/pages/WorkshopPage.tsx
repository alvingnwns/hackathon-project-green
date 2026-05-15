import { Suspense, useState } from 'react';
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

  // Local upload state — overrides Supabase data when present
  const [localData, setLocalData] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Blank state only when no local data has been loaded
  const isBlankState = projectId === 'blank' && !localData;
  const isErrorState = !isBlankState && !loading && error && !localData;

  // Effective data: localData takes priority over Supabase
  const effectiveData = localData ?? (projectData?.raw_json || null);

  const analysis = effectiveData?.project_context?.gemini_full_report?.analysis;
  const greenSolution = effectiveData?.project_context?.gemini_full_report?.green_solution;
  const assets: any[] = effectiveData?.assets || [];
  const hasData = assets.length > 0;

  // Loading state from Supabase fetch (not shown when uploading locally)
  if (loading && !isBlankState && !localData) {
    return (
      <div className='h-screen w-full flex flex-col overflow-hidden'>
        <HeaderWorkshopPage />
        <div className="flex flex-1 min-h-0 overflow-hidden" style={{ backgroundColor: 'var(--color-background)' }}>
          <WorkshopLeftBar onDataLoaded={setLocalData} isLoading={isUploading} setIsLoading={setIsUploading} />
          <div className="flex-1 flex items-center justify-center">
            <LoadingSpinner />
          </div>
          <WorkshopRightBar isBlank={true} />
        </div>
      </div>
    );
  }

  // Error/Not Found state (only when no local data)
  if (isErrorState) {
    return (
      <div className='h-screen w-full flex flex-col overflow-hidden'>
        <HeaderWorkshopPage />
        <div className="flex flex-1 min-h-0 overflow-hidden" style={{ backgroundColor: 'var(--color-background)' }}>
          <WorkshopLeftBar onDataLoaded={setLocalData} isLoading={isUploading} setIsLoading={setIsUploading} />
          <ProjectNotFound />
          <WorkshopRightBar isBlank={true} />
        </div>
      </div>
    );
  }

  // Middle panel content
  const renderMiddle = () => {
    if (isUploading) {
      return (
        <div className="flex-1 flex items-center justify-center" style={{ backgroundColor: 'var(--color-background)' }}>
          <div className="text-center space-y-4">
            <LoadingSpinner />
            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              Memproses gambar dengan AI...
            </p>
          </div>
        </div>
      );
    }
    if (hasData) {
      return (
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
      );
    }
    return <BlankCanvasPlaceholder />;
  };

  return (
    <div className='h-screen w-full flex flex-col overflow-hidden'>
      <HeaderWorkshopPage />
      <div className="flex flex-1 min-h-0 overflow-hidden" style={{ backgroundColor: 'var(--color-background)', color: 'var(--color-text-primary)' }}>
        <WorkshopLeftBar onDataLoaded={setLocalData} isLoading={isUploading} setIsLoading={setIsUploading} />

        {renderMiddle()}

        <WorkshopRightBar
          analysis={analysis}
          greenSolution={greenSolution}
          projectConcept={greenSolution?.concept_name}
          projectCost={greenSolution?.estimated_cost}
          isBlank={!hasData}
        />
      </div>
    </div>
  );
}