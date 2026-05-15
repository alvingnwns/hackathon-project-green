import { Suspense, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Canvas } from '@react-three/fiber';
import { useProject } from '../hooks/useProject';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { Scene } from '../components/workshop/Scene3D';
import WorkshopLeftBar from '../components/workshop/WorkshopLeftBar';
import WorkshopRightBar from '../components/workshop/WorkshopRightBar';
import HeaderWorkshopPage from '../components/HeaderWorkshopPage';

export default function WorkshopPage() {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('id');
  const { projectData, loading, error } = useProject(projectId);

  const [localData, setLocalData] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);

  const isBlankState = projectId === 'blank' && !localData;
  const isErrorState = !isBlankState && !loading && error && !localData;

  const effectiveData = localData ?? (projectData?.raw_json || null);
  const analysis = effectiveData?.project_context?.gemini_full_report?.analysis;
  const greenSolution = effectiveData?.project_context?.gemini_full_report?.green_solution;
  const assets: any[] = effectiveData?.assets || [];
  const hasData = assets.length > 0;

  return (
    <div className='h-screen w-full flex flex-col overflow-hidden'>
      <HeaderWorkshopPage />

      {/* Content area: relative container so absolute children fill it */}
      <div className='relative flex-1 overflow-hidden' style={{ background: '#111111' }}>

        {/* 3D Canvas: absolute inset-0 — same pattern as original App.jsx */}
        {hasData && !isUploading && (
          <div className='absolute inset-0'>
            <Canvas
              camera={{ position: [0, 6, 15], fov: 60 }}
              gl={{ antialias: true }}
            >
              <Suspense fallback={null}>
                <Scene assets={assets} />
              </Suspense>
            </Canvas>
          </div>
        )}

        {/* Uploading overlay */}
        {isUploading && (
          <div className='absolute inset-0 flex items-center justify-center' style={{ paddingLeft: '256px', paddingRight: '320px' }}>
            <div className='text-center space-y-4'>
              <LoadingSpinner />
              <p className='text-sm text-neutral-400'>Processing image with AI...</p>
            </div>
          </div>
        )}

        {/* Blank / loading / error state */}
        {!hasData && !isUploading && (
          <div className='absolute inset-0 flex items-center justify-center' style={{ paddingLeft: '256px', paddingRight: '320px' }}>
            {loading && !isBlankState ? (
              <LoadingSpinner />
            ) : isErrorState ? (
              <div className='text-center text-neutral-400'>
                <p className='text-lg font-semibold text-white'>Project not found</p>
                <p className='text-sm mt-1'>Invalid project ID or the project has been deleted.</p>
              </div>
            ) : (
              <div className='text-center text-neutral-400'>
                <div className='text-6xl mb-4'>🌱</div>
                <p className='text-xl font-semibold text-white'>Your soon-to-be-born masterpiece</p>
                <p className='text-sm mt-2 max-w-xs'>Upload an image or use mock data to start generating your 3D design</p>
              </div>
            )}
          </div>
        )}

        {/* Left sidebar: overlay */}
        <div className='absolute top-0 left-0 h-full z-10' style={{ width: '256px', backgroundColor: 'var(--color-surface)', borderRight: '1px solid var(--color-border)' }}>
          <WorkshopLeftBar
            onDataLoaded={setLocalData}
            isLoading={isUploading}
            setIsLoading={setIsUploading}
          />
        </div>

        {/* Right sidebar: overlay */}
        <div className='absolute top-0 right-0 h-full z-10 overflow-y-auto' style={{ width: '320px', backgroundColor: 'var(--color-surface)' }}>
          <WorkshopRightBar
            analysis={analysis}
            greenSolution={greenSolution}
            projectConcept={greenSolution?.concept_name}
            projectCost={greenSolution?.estimated_cost}
            isBlank={!hasData}
          />
        </div>

      </div>
    </div>
  );
}