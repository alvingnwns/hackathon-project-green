import io
import json
from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image
from pillow_heif import register_heif_opener
from core.config import settings

# Import semua engine kita
from services.ai_analyzer import analyze_landscape
from services.depth_engine import get_fov_from_exif, pixel_to_3d, depth_estimator
from services.vision_engine import find_target_object
import numpy as np

register_heif_opener()
router = APIRouter()

@router.post("/process-landscape")
async def process_landscape(file: UploadFile = File(...)):
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Format file tidak didukung.")

    try:
        # 1. Persiapan Gambar
        img_bytes = await file.read()
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        width, height = img.size

        # --- NODE 1: Analisis Gemini ---
        print("➡️ Menjalankan Node 1: Gemini Analysis...")
        analysis_json_str = analyze_landscape(img)
        analysis_result = json.loads(analysis_json_str)
        
        # Ekstrak target_area dari saran Gemini
        components = analysis_result.get("components_for_3d", [])
        target_label = "ground" # Fallback dasar
        
        if len(components) > 0:
            raw_target = components[0].get("target_area", "ground")
            # Pengaman bahasa
            if "LAHAN KOSONG" in raw_target.upper():
                target_label = "ground"
            else:
                target_label = raw_target

        # --- NODE 2 & 3: Vision Engine (Mencari Objek) ---
        print(f"➡️ Menjalankan Node 2: Mencari area '{target_label}'...")
        vision_data = find_target_object(img, target_label)

        if not vision_data:
            # Fallback jika objek gaib/tidak ketemu
            vision_data = {
                "label": target_label,
                "confidence": 0.0,
                "bounding_box": None,
                "center_coordinate": {"u": width // 2, "v": height // 2},
                "warning": "Objek tidak terdeteksi, menggunakan titik tengah fallback."
            }

        # --- NODE 5 & 6: Depth & Spatial Engine ---
        print("➡️ Menjalankan Node 5 & 6: Spatial Mapping...")
        dynamic_fov = get_fov_from_exif(img)
        
        # Eksekusi Depth-Anything
        depth_result = depth_estimator(img)
        depth_array = np.array(depth_result["depth"])
        
        # Ambil titik (u, v) dari hasil pencarian Vision Engine!
        target_u = vision_data["center_coordinate"]["u"]
        target_v = vision_data["center_coordinate"]["v"]
        
        # Pengaman agar koordinat tidak melebihi resolusi gambar
        target_u = min(max(target_u, 0), width - 1)
        target_v = min(max(target_v, 0), height - 1)
        
        target_z_raw = int(depth_array[target_v, target_u])

        # Kalkulasi ke X, Y, Z dunia nyata
        X, Y, Z_metric = pixel_to_3d(target_u, target_v, target_z_raw, width, height, fov_degrees=dynamic_fov)

        # --- FINAL RESPONSE ---
        return {
            "status": "success",
            "analysis": analysis_result,
            "vision_detection": vision_data,
            "spatial_placement": {
                "camera_fov": round(dynamic_fov, 2),
                "raw_depth_Z": target_z_raw,
                "final_3d_coordinates": {
                    "X_meter": X,
                    "Y_meter": Y,
                    "Z_meter": Z_metric
                }
            }
        }

    except Exception as e:
        print(f"Error di Router: {e}")
        raise HTTPException(status_code=500, detail=str(e))