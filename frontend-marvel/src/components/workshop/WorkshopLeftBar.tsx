export default function WorkshopLeftBar() {
  return (
    <div className="w-64 p-4 border-r" style={{ borderColor: 'var(--color-border)' }}>
      <button
        className="w-full mb-4 px-4 py-2 rounded-md font-medium transition"
        style={{ backgroundColor: 'var(--color-brand-green)', color: 'var(--color-text-inverse)' }}
      >
        Upload Image
      </button>
      <button
        className="w-full px-4 py-2 rounded-md font-medium transition"
        style={{
          backgroundColor: 'var(--color-surface-container)',
          color: 'var(--color-brand-green)',
          border: '1px solid var(--color-border)',
        }}
      >
        Upload Image using local JSON
      </button>
    </div>
  );
}
