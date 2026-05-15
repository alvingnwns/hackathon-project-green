export default function HeaderMainPage() {
  return (
    <header className="flex items-center justify-between mb-12">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--color-brand-green)' }}>
        GreenScape AI
      </h1>
      <div className="flex items-center gap-4">
        {/* Placeholder for Google Auth */}
        <button
          className="px-4 py-2 rounded-md text-sm transition"
          style={{
            backgroundColor: 'var(--color-background-tertiary)',
            color: 'var(--color-brand-green)',
            border: '1px solid var(--color-border)',
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.backgroundColor = 'var(--color-hover-neutral)')
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.backgroundColor = 'var(--color-background-tertiary)')
          }
        >
          Sign In with Google
        </button>
      </div>
    </header>
  );
}
