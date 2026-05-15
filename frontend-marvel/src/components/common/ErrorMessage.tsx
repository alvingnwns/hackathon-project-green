interface ErrorMessageProps {
  message: string;
  centered?: boolean;
}

export default function ErrorMessage({ message, centered = true }: ErrorMessageProps) {
  if (centered) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <div className="text-center">
          <div className="text-red-500 text-lg font-medium mb-2">Error</div>
          <div style={{ color: 'var(--color-text-secondary)' }}>{message}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 rounded-lg border px-4 py-3 text-sm" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface-container)', color: 'var(--color-text-secondary)' }}>
      {message}
    </div>
  );
}
