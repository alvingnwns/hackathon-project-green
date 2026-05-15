export default function ResultsBar() {
  return (
    <aside
      className="w-80 border-l p-4 shrink-0 overflow-y-auto"
      style={{
        backgroundColor: 'var(--color-background-secondary)',
        borderColor: 'var(--color-border)',
      }}
    >
      <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--color-brand-green)' }}>
        Results
      </h2>
      <div
        className="border-2 border-dashed h-32 rounded flex items-center justify-center text-sm"
        style={{
          borderColor: 'var(--color-border)',
          color: 'var(--color-text-light)',
        }}
      >
        Awaiting generation...
      </div>
    </aside>
  );
}
