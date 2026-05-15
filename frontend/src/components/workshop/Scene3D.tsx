import { Component, type ReactNode, useMemo, useState } from 'react';
import { useGLTF, OrbitControls, Environment } from '@react-three/drei';
import * as THREE from 'three';

// === Grid 3x3 Position System ===
const GRID_SPACING = 3.0;
const GRID_POSITIONS: Record<string, [number, number]> = Object.fromEntries(
  ['top', 'center', 'bottom'].flatMap((row, ri) =>
    ['left', 'center', 'right'].map((col, ci) => {
      const key = row === 'center' && col === 'center' ? 'center' : `${row}-${col}`;
      return [key, [(ci - 1) * GRID_SPACING, (ri - 1) * GRID_SPACING]];
    })
  )
);

const FALLBACK_HINTS = Object.keys(GRID_POSITIONS);
const GROUND_LEVEL = -2.0;

interface GLTFModelProps {
  url: string;
  index: number;
  scaleJSON?: number[];
  positionHint?: string;
  clusterCenter: [number, number, number];
}

function GLTFModel({ url, index, scaleJSON, positionHint, clusterCenter }: GLTFModelProps) {
  const { scene } = useGLTF(url);
  const isBase = index === 0;

  const hint =
    !isBase && positionHint && GRID_POSITIONS[positionHint]
      ? positionHint
      : FALLBACK_HINTS[Math.max(0, index - 1) % FALLBACK_HINTS.length];

  let finalX = isBase ? 0 : GRID_POSITIONS[hint][0];
  let finalZ = isBase ? 0 : GRID_POSITIONS[hint][1];

  const [randomRotationY] = useState(() => {
    if (isBase) return 0;
    const min = -10 * (Math.PI / 180);
    const max = 10 * (Math.PI / 180);
    return Math.random() * (max - min) + min;
  });

  let scaleArr = Array.isArray(scaleJSON) ? scaleJSON : [1, 1, 1];
  if (isBase) {
    if (clusterCenter) {
      finalX = clusterCenter[0];
      finalZ = clusterCenter[2];
    }
    scaleArr = [Math.max(scaleArr[0], 8.0), 5, Math.max(scaleArr[2], 8.0)];
  }

  const [sx, sy, sz] = scaleArr;

  const { clonedScene, offsetY, xzOffset } = useMemo(() => {
    const clone = scene.clone();
    clone.scale.set(sx, sy, sz);
    clone.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(clone);
    const cx = (box.min.x + box.max.x) / 2;
    const cz = (box.min.z + box.max.z) / 2;
    const xzOffset: [number, number] = isBase ? [-cx, -cz] : [0, 0];
    const calculatedOffset = isBase ? GROUND_LEVEL - box.max.y : GROUND_LEVEL - box.min.y;
    return { clonedScene: clone, offsetY: calculatedOffset, xzOffset };
  }, [scene, sx, sy, sz, isBase]);

  return (
    <group position={[finalX + xzOffset[0], offsetY, finalZ + xzOffset[1]]}>
      <primitive object={clonedScene} rotation={[0, randomRotationY, 0]} />
    </group>
  );
}

interface Asset {
  model_url: string | null;
  scale_3d?: number[];
  position_hint?: string;
}

const CAMERA_TARGET: [number, number, number] = [0, -2, 0];

// 3D Scene Component
export function Scene({ assets }: { assets: Asset[] }) {
  return (
    <>
      <ambientLight intensity={1.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} />
      <Environment preset="city" />
      <OrbitControls makeDefault target={CAMERA_TARGET} enableZoom={true} />
      {assets.map((asset, index) => {
        if (!asset.model_url) return null;
        return (
          <SceneErrorBoundary key={index}>
            <GLTFModel
              url={asset.model_url}
              index={index}
              scaleJSON={asset.scale_3d}
              positionHint={asset.position_hint}
              clusterCenter={CAMERA_TARGET}
            />
          </SceneErrorBoundary>
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
