import React, { useState, Suspense, useMemo } from "react";
import axios from "axios";
import * as THREE from "three";
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

// === Sistem Posisi Grid 3x3 ===
// Dikalkulasi dari rumus: 3 baris × 3 kolom dengan jarak GRID_SPACING meter.
// Tidak ada koordinat per-objek yang dihardcode — semua dihitung otomatis dari nama posisi.
const GRID_SPACING = 3.0;
const GRID_POSITIONS = Object.fromEntries(
  ["top", "center", "bottom"].flatMap((row, ri) =>
    ["left", "center", "right"].map((col, ci) => {
      const key = row === "center" && col === "center" ? "center" : `${row}-${col}`;
      return [key, [(ci - 1) * GRID_SPACING, (ri - 1) * GRID_SPACING]];
    })
  )
);
const FALLBACK_HINTS = Object.keys(GRID_POSITIONS);

// Komponen Sub untuk Me-render file GLB satuan
function GLTFModel({ url, index, scaleJSON, positionHint, clusterCenter }) {
  const { scene } = useGLTF(url);
  const isBase = index === 0;

  // Tentukan slot grid berdasarkan positionHint dari Gemini.
  // Jika hint tidak valid, fallback ke slot urutan berdasarkan index agar tidak overlap.
  const hint = (!isBase && positionHint && GRID_POSITIONS[positionHint])
    ? positionHint
    : FALLBACK_HINTS[Math.max(0, index - 1) % FALLBACK_HINTS.length];

  let finalX = isBase ? 0 : GRID_POSITIONS[hint][0];
  let finalZ = isBase ? 0 : GRID_POSITIONS[hint][1];

  // Rotasi acak antara -10 hingga 10 derajat untuk objek selain base
  const [randomRotationY] = useState(() => {
    if (isBase) return 0;
    const min = -10 * (Math.PI / 180);
    const max = 10 * (Math.PI / 180);
    return Math.random() * (max - min) + min;
  });

  // Skala dinamis
  let scaleArr = Array.isArray(scaleJSON) ? scaleJSON : [1, 1, 1];
  
  if (isBase) {
    if (clusterCenter) {
      finalX = clusterCenter[0];
      finalZ = clusterCenter[2];
    }
    // Lahan ditarik kembali ukurannya secara compact di 8x8 meter seperti arahan awal!
    scaleArr = [
      Math.max(scaleArr[0], 8.0), 
      5, 
      Math.max(scaleArr[2], 8.0)
    ]; 
  }

  const [sx, sy, sz] = scaleArr;

  // Pendekatan Matematika Fundamental: Mencari Bounding Box asli dari 3D Object.
  // Untuk base: hitung juga center XZ agar model selalu terpusat di world origin,
  // tidak bergantung pada letak origin internal model GLB (yang sering tidak di tengah).
  const { clonedScene, offsetY, xzOffset } = useMemo(() => {
    const clone = scene.clone();
    clone.scale.set(sx, sy, sz);
    clone.updateMatrixWorld(true);

    const box = new THREE.Box3().setFromObject(clone);
    const objectBottom = box.min.y;
    const objectTop = box.max.y;
    const GROUND_LEVEL = -2.0;
    
    const calculatedOffset = isBase ? (GROUND_LEVEL - objectTop) : (GROUND_LEVEL - objectBottom);

    // Hitung geser XZ agar model base selalu berpusat di (0, _, 0)
    const cx = (box.min.x + box.max.x) / 2;
    const cz = (box.min.z + box.max.z) / 2;
    const xzOffset = isBase ? [-cx, -cz] : [0, 0];
    
    return { clonedScene: clone, offsetY: calculatedOffset, xzOffset };
  }, [scene, sx, sy, sz, isBase]);

  return (
    <group position={[finalX + xzOffset[0], offsetY, finalZ + xzOffset[1]]}>
      <primitive object={clonedScene} rotation={[0, randomRotationY, 0]} />
    </group>
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
      if (error.response && error.response.status === 400 && error.response.data?.detail) {
        // Tampilkan pesan alasan rejection dari backend (is_already_green)
        alert("INFO: " + error.response.data.detail);
      } else {
        alert("Terjadi kesalahan sistem saat memproses gambar.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseMockData = () => {
    setResultData(mockData);
  };

  const handleJSONUpload = (e) => {
    const fileObj = e.target.files[0];
    if (!fileObj) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsedJSON = JSON.parse(event.target.result);
        if (parsedJSON.assets) {
          setResultData(parsedJSON);
        } else {
          alert("Format JSON sepertinya tidak sesuai dengan struktur aplikasi.");
        }
      } catch {
        alert("Gagal membaca file JSON: Format tidak valid.");
      }
    };
    reader.readAsText(fileObj);
  };

  // Grid 3x3 terpusat di origin — kamera selalu mengarah ke pusat scene
  const cameraTarget = [0, -2, 0];

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
        
        <Canvas camera={{ position: [cameraTarget[0], cameraTarget[1] + 8, cameraTarget[2] + 15], fov: 60 }}>
          <ambientLight intensity={1.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} />
          <Environment preset="city" />
          <OrbitControls makeDefault target={cameraTarget} />

          {/* Render Komponen 3D Asli dari JSON */}
          <Suspense fallback={null}>
            {resultData && resultData.assets?.map((asset, index) => {
              if (!asset.model_url) return null;
              
              return (
                <ErrorBoundary key={index}>
                  <GLTFModel 
                    url={asset.model_url} 
                    index={index}
                    scaleJSON={asset.scale_3d}
                    positionHint={asset.position_hint}
                    clusterCenter={cameraTarget}
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
            className="w-full py-2 mb-2 rounded-lg font-bold text-emerald-300 border border-emerald-500 hover:bg-emerald-900/50 transition-all shadow-lg"
          >
            Gunakan Data JSON Lokal (Hemat API)
          </button>

          <label className="w-full py-2 rounded-lg font-bold text-neutral-300 border border-neutral-500 hover:bg-neutral-700/50 transition-all shadow-lg cursor-pointer flex justify-center items-center text-center">
            📄 Upload History JSON
            <input 
              type="file" 
              accept=".json" 
              onChange={handleJSONUpload}
              className="hidden"
            />
          </label>
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

