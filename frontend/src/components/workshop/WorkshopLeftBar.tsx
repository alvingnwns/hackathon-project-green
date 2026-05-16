import { useRef, useState } from 'react';

interface WorkshopLeftBarProps {
  onDataLoaded: (data: any) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export default function WorkshopLeftBar({ onDataLoaded, isLoading, setIsLoading }: WorkshopLeftBarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const jsonInputRef = useRef<HTMLInputElement>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [dryRun, setDryRun] = useState(true); // default ON to protect Meshy credits

  const handleImageUpload = async (file: File) => {
    setIsLoading(true);
    setUploadStatus(dryRun ? 'Simulation mode — skipping Meshy API...' : 'Analyzing image with AI...');
    const formData = new FormData();
    formData.append('file', file);

    const url = dryRun
      ? 'http://127.0.0.1:8000/api/v1/process-landscape?dry_run=true'
      : 'http://127.0.0.1:8000/api/v1/process-landscape';

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        alert('Error: ' + ((err as any).detail || 'An error occurred while processing the image'));
        return;
      }

      const data = await response.json();
      onDataLoaded(data);
      setUploadStatus(null);
    } catch {
      alert('Cannot connect to server. Make sure the backend is running on port 8000.');
      setUploadStatus(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMockData = async () => {
    const { default: mockData } = await import('../../mockData.json');
    onDataLoaded(mockData);
  };

  const handleJSONUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        if (parsed.assets) {
          onDataLoaded(parsed);
        } else {
          alert('Invalid JSON format. Must contain an "assets" field.');
        }
      } catch {
        alert('Failed to read JSON file. Make sure the file format is valid.');
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="w-64 p-4 border-r flex flex-col gap-3" style={{ borderColor: 'var(--color-border)' }}>
      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/heic,image/heif"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && handleImageUpload(e.target.files[0])}
        onClick={(e) => { (e.target as HTMLInputElement).value = ''; }}
      />
      <input
        ref={jsonInputRef}
        type="file"
        accept=".json"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && handleJSONUpload(e.target.files[0])}
        onClick={(e) => { (e.target as HTMLInputElement).value = ''; }}
      />

      {/* Upload Image Button */}
      <button
        className="w-full px-4 py-2 rounded-md font-medium transition disabled:opacity-50"
        style={{ backgroundColor: 'var(--color-brand-green)', color: 'var(--color-text-inverse)' }}
        onClick={() => fileInputRef.current?.click()}
        disabled={isLoading}
      >
        {isLoading ? 'Processing...' : 'Upload Image'}
      </button>

      {/* Simulation Mode toggle */}
      <label className="flex items-center gap-2 cursor-pointer select-none" title="Simulation mode: skips Meshy API and uses stock GLBs. Disable only for production.">
        <div
          className="relative w-9 h-5 rounded-full transition-colors"
          style={{ backgroundColor: dryRun ? 'var(--color-brand-green)' : 'var(--color-border)' }}
          onClick={() => setDryRun(v => !v)}
        >
          <div
            className="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform"
            style={{ transform: dryRun ? 'translateX(1.25rem)' : 'translateX(0.125rem)' }}
          />
        </div>
        <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          {dryRun ? '🧪 Simulation Mode' : '🚀 Production Mode'}
        </span>
      </label>

      {/* Use Mock Data Button */}
      <button
        className="w-full px-4 py-2 rounded-md font-medium transition disabled:opacity-50"
        style={{
          backgroundColor: 'var(--color-surface-container)',
          color: 'var(--color-brand-green)',
          border: '1px solid var(--color-border)',
        }}
        onClick={handleMockData}
        disabled={isLoading}
      >
        Use Mock Data
      </button>

      {/* Upload JSON Button */}
      <button
        className="w-full px-4 py-2 rounded-md font-medium transition disabled:opacity-50"
        style={{
          backgroundColor: 'var(--color-surface-container)',
          color: 'var(--color-brand-green)',
          border: '1px solid var(--color-border)',
        }}
        onClick={() => jsonInputRef.current?.click()}
        disabled={isLoading}
      >
        Upload JSON History
      </button>

      {/* Status text */}
      {uploadStatus && (
        <p className="text-xs text-center mt-2" style={{ color: 'var(--color-text-secondary)' }}>
          {uploadStatus}
        </p>
      )}
    </div>
  );
}

