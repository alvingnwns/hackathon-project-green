export default function UtilitiesBar() {
  return (
    <aside
      className="w-64 border-r p-4 shrink-0 overflow-y-auto"
      style={{
        backgroundColor: 'var(--color-background-secondary)',
        borderColor: 'var(--color-border)',
      }}
    >
      <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--color-brand-green)' }}>
        Utilities
      </h2>
      <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
        Upload land photos and configure landscape settings here.
      </p>
      {/* Buttons and inputs go here */}
    </aside>
  );
}
