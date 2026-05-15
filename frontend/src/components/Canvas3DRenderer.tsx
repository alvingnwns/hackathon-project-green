export default function Canvas3DRenderer() {
  return (
    <main
      className="flex-1 relative"
      style={{ backgroundColor: 'var(--color-background-tertiary)' }}
    >
      <div
        className="absolute inset-0 flex flex-col items-center justify-center"
        style={{ color: 'var(--color-text-light)' }}
      >
        <p className="mb-2">3D Landscape Canvas Area</p>
        <p className="text-xs" style={{ color: 'var(--color-text-light)' }}>
          (React Three Fiber will mount here)
        </p>
      </div>
    </main>
  );
}
