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

  const handleImageUpload = async (file: File) => {
    setIsLoading(true);
    setUploadStatus('Menganalisis gambar dengan AI...');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/v1/process-landscape', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        alert('Error: ' + ((err as any).detail || 'Terjadi kesalahan saat memproses gambar'));
        return;
      }

      const data = await response.json();
      onDataLoaded(data);
      setUploadStatus(null);
    } catch {
      alert('Tidak dapat terhubung ke server. Pastikan backend berjalan di port 8000.');
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
          alert('Format JSON tidak sesuai. Harus memiliki field "assets".');
        }
      } catch {
        alert('Gagal membaca file JSON. Pastikan format file valid.');
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
        {isLoading ? 'Memproses...' : 'Upload Image'}
      </button>

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
        Gunakan Mock Data
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

