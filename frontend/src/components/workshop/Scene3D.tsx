import { Component, type ReactNode, useMemo, useState } from 'react';
import { useGLTF, OrbitControls, Environment } from '@react-three/drei';
import * as THREE from 'three';

// === Grid 3x3 Position System (base spacing — scaled dynamically per scene) ===
const GRID_SPACING = 3.0;
const HINT_ORDER = ['top-left','top-center','top-right','center-left','center','center-right','bottom-left','bottom-center','bottom-right'] as const;
const GROUND_LEVEL = -2.0;
const AABB_PADDING = 0.8; // clearance (world units) between model footprints

/**
 * Minimum visual ratio: any non-base model whose largest dimension is below
 * this fraction of the scene's largest non-base model gets scaled up uniformly.
 * Prevents large-scale models (e.g. a greenhouse) from making smaller assets
 * (e.g. bins, panels) visually invisible. Base terrain (index 0) is never touched.
 */
const MIN_VISUAL_RATIO = 0.20;

function normalizeScales(assets: Asset[]): number[][] {
  const scales = assets.map(a => Array.isArray(a.scale_3d) ? [...a.scale_3d] : [1, 1, 1]);
  const maxDim = scales.slice(1).reduce((m, s) => Math.max(m, s[0], s[1], s[2]), 0);
  if (maxDim === 0) return scales;
  return scales.map((s, i) => {
    if (i === 0) return s; // base terrain — never modify
    const modelMax = Math.max(s[0], s[1], s[2]);
    const ratio = modelMax / maxDim;
    if (ratio < MIN_VISUAL_RATIO) {
      const factor = (MIN_VISUAL_RATIO * maxDim) / modelMax;
      return [s[0] * factor, s[1] * factor, s[2] * factor];
    }
    return s;
  });
}

/** Build a 3×3 grid of candidate XZ positions scaled by `spacing`. */
function buildGrid(spacing: number): [number, number][] {
  const slots: [number, number][] = [];
  for (let ri = 0; ri < 3; ri++)
    for (let ci = 0; ci < 3; ci++)
      slots.push([(ci - 1) * spacing, (ri - 1) * spacing]);
  return slots; // order matches HINT_ORDER
}

/**
 * Pre-compute non-overlapping XZ positions using AABB footprints.
 *
 * Grid spacing is computed dynamically from the largest non-base model so that
 * adjacent slots always have enough room. The terrain half-extent needed to
 * cover all placements is returned alongside positions so the caller can
 * auto-scale the base terrain.
 */
function resolvePositions(assets: Asset[], scales: number[][]): { positions: [number, number][]; terrainHalf: number } {
  // Dynamic spacing: must fit the widest non-base model twice + clearance
  const maxHalf = assets.slice(1).reduce(
    (m, _, j) => Math.max(m, scales[j + 1][0] / 2, scales[j + 1][2] / 2),
    0
  );
  const spacing = Math.max(GRID_SPACING, maxHalf * 2 + AABB_PADDING * 2);
  const gridSlots = buildGrid(spacing);

  const positions: [number, number][] = [];

  const hasOverlap = (i: number, x: number, z: number) => {
    const hx = scales[i][0] / 2;
    const hz = scales[i][2] / 2;
    return positions.some(([ox, oz], pi) => {
      if (pi === 0) return false; // base terrain — skip
      const ohx = scales[pi][0] / 2;
      const ohz = scales[pi][2] / 2;
      return (
        Math.abs(x - ox) < hx + ohx + AABB_PADDING &&
        Math.abs(z - oz) < hz + ohz + AABB_PADDING
      );
    });
  };

  for (let i = 0; i < assets.length; i++) {
    if (i === 0) { positions.push([0, 0]); continue; }

    // Pick starting slot from hint (mapped to HINT_ORDER index)
    const hintIdx = assets[i].position_hint
      ? HINT_ORDER.indexOf(assets[i].position_hint as typeof HINT_ORDER[number])
      : -1;
    let [cx, cz] = hintIdx >= 0
      ? gridSlots[hintIdx]
      : gridSlots[(i - 1) % gridSlots.length];

    if (hasOverlap(i, cx, cz)) {
      // Try all grid slots in HINT_ORDER
      let placed = false;
      for (const [tx, tz] of gridSlots) {
        if (!hasOverlap(i, tx, tz)) { cx = tx; cz = tz; placed = true; break; }
      }
      if (!placed) {
        // Spiral outward beyond the 3×3 grid
        outer: for (let ring = 1; ring <= 6; ring++) {
          const r = spacing * (ring + 1);
          const steps = 8 * ring;
          for (let s = 0; s < steps; s++) {
            const angle = (s * Math.PI * 2) / steps;
            const tx = Math.cos(angle) * r;
            const tz = Math.sin(angle) * r;
            if (!hasOverlap(i, tx, tz)) { cx = tx; cz = tz; break outer; }
          }
        }
      }
    }

    positions.push([cx, cz]);
  }

  // Terrain must cover every placed model + a margin
  const terrainHalf = positions.reduce((m, [x, z], i) => {
    if (i === 0) return m;
    const hx = scales[i][0] / 2;
    const hz = scales[i][2] / 2;
    return Math.max(m, Math.abs(x) + hx + 2, Math.abs(z) + hz + 2);
  }, 4);

  return { positions, terrainHalf };
}

interface GLTFModelProps {
  url: string;
  index: number;
  scaleJSON?: number[];
  position: [number, number]; // pre-resolved XZ (overlap-free)
  clusterCenter: [number, number, number];
  /** For base terrain only: world-space half-extent to cover all placed models */
  terrainHalf?: number;
}

function GLTFModel({ url, index, scaleJSON, position, clusterCenter, terrainHalf }: GLTFModelProps) {
  const { scene } = useGLTF(url);
  const isBase = index === 0;

  let [finalX, finalZ] = position;

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
    // Auto-expand terrain to cover all placed models
    const minExtent = terrainHalf != null ? terrainHalf * 2 : 8.0;
    scaleArr = [Math.max(scaleArr[0], minExtent), 5, Math.max(scaleArr[2], minExtent)];
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
  // normalizedScales: auto-scale up models that are too small relative to the largest
  const normalizedScales = useMemo(() => normalizeScales(assets), [assets]);
  const { positions, terrainHalf } = useMemo(
    () => resolvePositions(assets, normalizedScales),
    [assets, normalizedScales]
  );

  return (
    <>
      <color attach="background" args={['#111111']} />
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
              scaleJSON={normalizedScales[index]}
              position={positions[index] ?? [0, 0]}
              clusterCenter={CAMERA_TARGET}
              terrainHalf={index === 0 ? terrainHalf : undefined}
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
