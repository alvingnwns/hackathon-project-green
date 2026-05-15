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

// Komponen Sub untuk Me-render file GLB satuan
function GLTFModel({ url, positionJSON, index, scaleJSON, clusterCenter }) {
  // Pemuat GLTF (cached otomatis oleh Drei)
  const { scene } = useGLTF(url);
  
  // Ambil data X, Y, Z dari Backend (Depth Engine) dengan optional chaining
  // Tambahkan faktor pengali (multiplier) yang lebih besar agar jarak spasial lebih terpisah secara arsitektural (spread out)
  const rawX = positionJSON?.X_meter || 0;
  const rawZ = positionJSON?.Z_meter || 5;

  let finalX = rawX * 3.0; 
  let finalZ = -rawZ * 2.5; 

  // Cek apakah ini Base Ground (Lahan). Di JSON, id bisa 0 atau 1, tapi biasanya elemen paling pertama adalah alas.
  const isBase = index === 0;

  // Rotasi acak antara -10 hingga 10 derajat untuk objek selain base
  // Dibungkus useState agar tidak dicomplain React Compiler (Math.random is impure during render)
  const [randomRotationY] = useState(() => {
    if (isBase) return 0;
    const min = -10 * (Math.PI / 180);
    const max = 10 * (Math.PI / 180);
    return Math.random() * (max - min) + min;
  });

  // Fallback Grid Arsitektural: 
  if (!isBase) {
    // Buat formasi U-shape atau Grid Box
    const col = (index - 1) % 3; 
    const row = Math.floor((index - 1) / 3);
    finalX = finalX + ((col - 1) * 2.5);
    finalZ = finalZ - (row * 2.5);
  }

  // Skala dinamis
  let scaleArr = Array.isArray(scaleJSON) ? scaleJSON : [1, 1, 1];
  
  if (isBase) {
    if (clusterCenter) {
      finalX = clusterCenter[0];
      finalZ = clusterCenter[2];
    }
    // Pastikan alas (lahan) minimal melebar jauh untuk mencakup area. 
    scaleArr = [
      Math.max(scaleArr[0], 8.0), 
      5, 
      Math.max(scaleArr[2], 8.0)
    ]; 
  }

  const [sx, sy, sz] = scaleArr;

  // Pendekatan Matematika Fundamental: Mencari Bounding Box asli dari 3D Object
  // Semua kalkulasi box & offset dilakukan tanpa mengubah dependency lokal secara reaktif
  const { clonedScene, offsetY } = useMemo(() => {
    const clone = scene.clone();
    clone.scale.set(sx, sy, sz);
    clone.updateMatrixWorld(true);

    const box = new THREE.Box3().setFromObject(clone);
    const objectBottom = box.min.y;
    const objectTop = box.max.y;
    const GROUND_LEVEL = -2.0;
    
    const calculatedOffset = isBase ? (GROUND_LEVEL - objectTop) : (GROUND_LEVEL - objectBottom);
    
    return { clonedScene: clone, offsetY: calculatedOffset };
  }, [scene, sx, sy, sz, isBase]);

  return (
    <group position={[finalX, offsetY, finalZ]}>
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
      } catch (error) {
        alert("Gagal membaca file JSON: Format tidak valid.");
      }
    };
    reader.readAsText(fileObj);
  };

  // Kalkulasi target kamera yang akurat di tengah-tengah seluruh objek yang degenerate
  const getCameraTarget = () => {
    if (!resultData?.assets || resultData.assets.length === 0) return [0, -2, 0];
    let sumX = 0;
    let sumZ = 0;
    let validCount = 0;

    resultData.assets.forEach((asset, index) => {
      const pos = asset.spatial_data?.spatial_3d_coordinates;
      if (pos) {
        const x = (pos.X_meter || 0) * 1.5; 
        const finalX = Math.abs(x) < 0.1 ? (index % 3 - 1) * 2 : x;
        const z = -(pos.Z_meter || 5) * 1.5 - ((Math.floor(index / 3)) * 1.5);
        sumX += finalX;
        sumZ += z;
        validCount++;
      }
    });

    if (validCount === 0) return [0, -2, 0];
    // Offset orbit anchor sedikit ke belakang dan turun (karena anchor y=-2)
    return [sumX / validCount, -2, sumZ / validCount];
  };

  const cameraTarget = getCameraTarget();
  const baseAsset = resultData?.assets?.find(a => a.asset_id === 0);
  const baseAnchorY = baseAsset?.spatial_data?.spatial_3d_coordinates?.Y_meter || 0;

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
                    // Ambil koordinat 'relative_position' yang dibuat Gemini
                    positionJSON={asset.spatial_data?.spatial_3d_coordinates} 
                    index={index}
                    // Ambil 'scale_3d' yang sudah dipikirkan rasionya oleh Gemini
                    scaleJSON={asset.scale_3d}
                    clusterCenter={cameraTarget}
                    baseAnchorY={baseAnchorY}
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

