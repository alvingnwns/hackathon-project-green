import { Sparkles } from 'lucide-react';

export default function BlankCanvasPlaceholder() {
  return (
    <div className="flex-1 flex items-center justify-center bg-gray-100">
      <div className="text-center space-y-4">
        <div className="flex justify-center">
          <Sparkles size={64} className="text-yellow-500" />
        </div>
        <h2 className="text-2xl font-bold text-gray-600">
          Your soon-to-be-born masterpiece
        </h2>
        <p className="text-gray-500 max-w-md">
          Upload an image or JSON file to start creating your green architecture project
        </p>
      </div>
    </div>
  );
}