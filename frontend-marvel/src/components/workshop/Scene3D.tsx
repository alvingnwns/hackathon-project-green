import { Component, type ReactNode } from 'react';
import { useGLTF, OrbitControls } from '@react-three/drei';

function Model({ url, position }: { url: string; position: [number, number, number] }) {
  const { scene } = useGLTF(url);
  return <primitive object={scene} position={position} />;
}

// 3D Scene Component
export function Scene({ assets }: { assets: any[] }) {
  return (
    <>
      <ambientLight intensity={1.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} />
      <OrbitControls enableZoom={true} />
      {assets.map((asset, index) => {
        const coords = asset.spatial_data?.spatial_3d_coordinates;
        if (!coords) return null;
        return (
          <Model
            key={index}
            url={asset.model_url}
            position={[coords.X_meter, coords.Y_meter, coords.Z_meter]}
          />
        );
      })}
    </>
  );
}

// Error Boundary for 3D Scene
export class SceneErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error('3D scene error:', error);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-full items-center justify-center p-6" style={{ color: 'var(--color-text-inverse)' }}>
          <div>
            <p className="text-lg font-semibold">3D scene failed to load</p>
            <p className="text-sm text-neutral-300">Check the model URLs and try again.</p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
