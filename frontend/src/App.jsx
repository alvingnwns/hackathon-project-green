import React, { useState, Suspense } from "react";
import axios from "axios";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Environment, useGLTF } from "@react-three/drei";
import mockData from "./mockData.json";

// Error Boundary untuk menangkap eror dari load GLB (seperti CORS atau 404) agar tidak blank putih
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error("3D Render Error: ", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <mesh>
          <boxGeometry args={[1, 1, 1]} />
          <meshStandardMaterial color="red" wireframe />
        </mesh>
      );
    }
    return this.props.children;
  }
}

// Komponen Sub untuk Me-render file GLB satuan
function GLTFModel({ url, positionJSON }) {
  // Pemuat GLTF (cached otomatis oleh Drei)
  const { scene } = useGLTF(url);
  
  // Ambil data X, Y, Z dari Backend (Depth Engine) dengan optional chaining
  const x = positionJSON?.X_meter || 0;
  const y = positionJSON?.Y_meter || 0;
  const z = positionJSON?.Z_meter || -5; // Default agak ke depan kamera

  // Pendekatan Arsitektural: Dibuat presisi dan seragam tanpa nilai acak 
  // agar terlihat seperti maket perancangan kota / master plan yang profesional.
  return (
    <primitive 
      object={scene.clone()} // Clone agar bisa dipakai berulang jika model sama
      position={[x, y, z]} 
      rotation={[0, 0, 0]} // Semua menghadap arah grid secara teratur
      scale={[1, 1, 1]}    // Skala 1:1 sesuai metrik asli objeknya
    />
  );
}

function App() {
  const [file, setFile] = useState(null);
  const [previewURL, setPreviewURL] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [resultData, setResultData] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setPreviewURL(URL.createObjectURL(e.target.files[0]));
      setResultData(null); // Reset hasil saat pilih gambar baru
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Endpoint ke FastAPI Backend
      const res = await axios.post("http://localhost:8000/api/v1/process-landscape", formData);
      setResultData(res.data);
    } catch (error) {
      console.error("Error processing landscape:", error);
      alert("Terjadi kesalahan saat memproses gambar.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseMockData = () => {
    setResultData(mockData);
  };

  return (
    <div className="relative w-screen h-screen bg-neutral-900 text-white overflow-hidden">
      
      {/* 3D Canvas Background Layer */}
      <div className="absolute inset-0 z-0 pointer-events-auto">
        {previewURL && (
          <img 
            src={previewURL} 
            alt="Landscape Preview" 
            className="absolute inset-0 w-full h-full object-cover opacity-30" 
          />
        )}
        <Canvas camera={{ position: [0, 5, 10], fov: 60 }}>
          <ambientLight intensity={1.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} />
          <Environment preset="city" />
          <OrbitControls makeDefault />

          {/* Render Komponen 3D Asli dari JSON */}
          <Suspense fallback={null}>
            {resultData && resultData.assets?.map((asset, index) => {
              if (!asset.model_url) return null; // Lewati jika gagal generate
              
              // Jika ini URL Meshy (yang kena CORS), proxy lewat backend. 
              // Jika sudah berada di Supabase (tidak kena CORS), bisa dirender langsung!
              const isMeshy = asset.model_url.includes("meshy.ai");
              const safeUrl = isMeshy 
                ? `http://localhost:8000/api/v1/proxy-glb?url=${encodeURIComponent(asset.model_url)}` 
                : asset.model_url;
              
              return (
                <ErrorBoundary key={index}>
                  <GLTFModel 
                    url={safeUrl} 
                    positionJSON={asset.spatial_data?.spatial_3d_coordinates} 
                  />
                </ErrorBoundary>
              );
            })}
          </Suspense>

        </Canvas>
      </div>

      {/* UI Overlay Layer (Sidebar Kanan) */}
      <div className="absolute top-0 right-0 h-full w-full max-w-md z-10 pointer-events-none p-6 flex flex-col gap-4 overflow-y-auto">
        
        {/* Header / Upload Box */}
        <div className="bg-neutral-800/90 backdrop-blur-md p-6 rounded-2xl shadow-xl w-full pointer-events-auto border border-neutral-700 shrink-0">
          <h1 className="text-2xl font-bold mb-2 text-emerald-400">Green Landscape AI</h1>
          <p className="text-sm text-neutral-300 mb-6">Unggah foto lahan kosong untuk melihat transformasi desain lanskap 3D secara presisi.</p>
          
          <input 
            type="file" 
            accept="image/*" 
            onChange={handleFileChange}
            className="block w-full text-sm text-neutral-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-emerald-500 file:text-white hover:file:bg-emerald-600 mb-4 cursor-pointer"
          />

          <button 
            onClick={handleUpload}
            disabled={!file || isLoading}
            className={`w-full py-3 rounded-lg font-bold text-white transition-all shadow-lg mb-3 ${
              !file || isLoading ? "bg-neutral-600 cursor-not-allowed" : "bg-emerald-600 hover:bg-emerald-500 hover:scale-[1.02]"
            }`}
          >
            {isLoading ? "Memproses AI (Memakan waktu)..." : "Mulai Generate Desain!"}
          </button>
          
          <button 
            onClick={handleUseMockData}
            className="w-full py-2 rounded-lg font-bold text-emerald-300 border border-emerald-500 hover:bg-emerald-900/50 transition-all shadow-lg"
          >
            Gunakan Data JSON Lokal (Hemat API)
          </button>
        </div>

        {/* Results Info Overlay */}
        {resultData && (
          <div className="bg-neutral-800/90 backdrop-blur-md p-6 rounded-2xl shadow-xl w-full pointer-events-auto border border-emerald-800/50 shrink-0 flex-1 flex flex-col min-h-0">
             <h2 className="text-lg font-bold text-emerald-300 mb-1 leading-tight">{resultData.project_context?.concept || "Konsep Lanskap"}</h2>
             <p className="text-xs text-emerald-500/70 font-semibold mb-4">Total Aset: {resultData.assets?.length || 0} Model 3D</p>
             
             {/* List Asset */}
             <div className="overflow-y-auto pr-2 flex-1 space-y-3">
                {resultData.assets?.map((asset, i) => (
                  <div key={i} className="p-3 bg-neutral-900/80 rounded-lg border border-neutral-700/50">
                    <div className="font-semibold text-emerald-200 text-sm mb-1">#{asset.asset_id} {asset.name?.split(":")[0] || asset.name}</div>
                    <div className="text-xs text-neutral-400">{asset.name?.split(":")[1] || ""}</div>
                    <div className="mt-2 text-[10px] text-neutral-500 flex justify-between">
                      <span>Label: {asset.vision_detection?.label || "N/A"}</span>
                      <span>X: {asset.spatial_data?.spatial_3d_coordinates?.X_meter?.toFixed(2)}, Y: {asset.spatial_data?.spatial_3d_coordinates?.Y_meter?.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
             </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;

