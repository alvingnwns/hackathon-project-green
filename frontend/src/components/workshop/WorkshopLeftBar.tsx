import { useRef, useState, useCallback } from 'react';

const POLL_INTERVAL_MS = 2000; // Poll every 2 seconds
const BACKEND_URL = 'http://127.0.0.1:8000/api/v1';

interface TaskPayload {
  assets?: unknown[];
  [key: string]: unknown;
}

interface WorkshopLeftBarProps {
  onDataLoaded: (data: TaskPayload) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  onProgressUpdate?: (progress: string) => void;
}

export default function WorkshopLeftBar({ onDataLoaded, isLoading, setIsLoading, onProgressUpdate }: WorkshopLeftBarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const jsonInputRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef<number | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [dryRun, setDryRun] = useState(true); // default ON to protect Modal credits

  // Cleanup polling on unmount
  const stopPolling = useCallback(() => {
    if (pollingRef.current !== null) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const pollTask = useCallback(async (taskId: string) => {
    try {
      const response = await fetch(`${BACKEND_URL}/tasks/${taskId}`);
      if (!response.ok) {
        throw new Error(`Polling failed: ${response.status}`);
      }

      const taskData = await response.json();
      
      // Update progress
      const progressMsg = taskData.progress || '';
      setUploadStatus(progressMsg);
      onProgressUpdate?.(progressMsg);

      if (taskData.status === 'completed') {
        stopPolling();
        if (taskData.result) {
          onDataLoaded(taskData.result);
        } else if (taskData.result?.is_already_green) {
          alert(taskData.result.rejection_reason || 'This image is already a green ecosystem.');
        }
        setUploadStatus(null);
        setIsLoading(false);
      } else if (taskData.status === 'failed') {
        stopPolling();
        alert(`Pipeline failed: ${taskData.error || 'Unknown error'}`);
        setUploadStatus(null);
        setIsLoading(false);
      }
      // If status is 'queued' or 'processing', keep polling
    } catch (err) {
      stopPolling();
      alert(`Cannot connect to server: ${err}`);
      setUploadStatus(null);
      setIsLoading(false);
    }
  }, [onDataLoaded, setIsLoading, onProgressUpdate, stopPolling]);

  const handleImageUpload = async (file: File) => {
    setIsLoading(true);
    setUploadStatus('Starting pipeline...');
    const formData = new FormData();
    formData.append('file', file);

    const url = dryRun
      ? `${BACKEND_URL}/process-landscape?dry_run=true`
      : `${BACKEND_URL}/process-landscape`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        const errData = err as Record<string, string>;
        alert('Error: ' + (errData.detail || 'An error occurred while processing the image'));
        setIsLoading(false);
        setUploadStatus(null);
        return;
      }

      // Get task_id and start polling
      const taskResponse = await response.json();
      const taskId = taskResponse.task_id;
      
      setUploadStatus('Pipeline queued. Processing your image...');
      
      // Start polling
      pollingRef.current = window.setInterval(() => {
        pollTask(taskId);
      }, POLL_INTERVAL_MS);

    } catch {
      alert('Cannot connect to server. Make sure the backend is running on port 8000.');
      setUploadStatus(null);
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
      <label className="flex items-center gap-2 cursor-pointer select-none" title="Simulation mode: skips Modal.com GPU pipeline and uses stock GLBs. Disable only for production.">
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

      {/* Progress Status */}
      {uploadStatus && (
        <div className="mt-2 space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-400 animate-pulse" />
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
              Processing...
            </p>
          </div>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
            {uploadStatus}
          </p>
        </div>
      )}
    </div>
  );
}