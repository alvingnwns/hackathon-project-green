import io
import json
from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image
from pillow_heif import register_heif_opener
from core.config import settings

# Import semua engine kita
from services.ai_analyzer import analyze_landscape
from services.depth_engine import get_fov_from_exif, pixel_to_3d, depth_estimator, extract_depth_at_pixel
from services.vision_engine import find_target_object
from services.meshy_engine import generate_multiple_models
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
        
        # Ekstrak komponen dari saran Gemini
        components = analysis_result.get("components_for_3d", [])
        
        # Proses pipeline paralel untuk Multi-Object
        processed_components = []
        prompts_to_generate = []

        if not components:
            # Fallback jika kosong
            components = [{"to_generate": "bamboo pavilion", "target_area": "ground", "description": "Fallback asset"}]

        for idx, item in enumerate(components):
            prompt_3d = item.get("to_generate", "building")
            raw_target = item.get("target_area", "ground")
            position_hint = item.get("position_hint", "middle")
            
            # Pengaman bahasa
            target_label = "ground" if "LAHAN KOSONG" in raw_target.upper() else raw_target

            # --- NODE 2 & 3: Vision Engine (Mencari Objek O C) ---
            print(f"➡️ Menjalankan Node 2: Mencari area '{target_label}' untuk objek '{prompt_3d}'...")
            vision_data = find_target_object(img, target_label, position_hint)

            if not vision_data:
                vision_data = {
                    "label": target_label,
                    "confidence": 0.0,
                    "bounding_box": None,
                    "center_coordinate": {"u": width // 2, "v": height // 2},
                    "warning": "Objek tidak terdeteksi, menggunakan titik tengah fallback."
                }

            # --- NODE 5 & 6: Depth & Spatial Engine ---
            print(f"➡️ Menjalankan Node 5 & 6: Spatial Mapping untuk '{prompt_3d}'...")
            target_u = vision_data["center_coordinate"]["u"]
            target_v = vision_data["center_coordinate"]["v"]
            
            spatial_data = extract_depth_at_pixel(img, target_u, target_v)

            # Simpan sementara komponen yang sudah punya koordinat
            processed_components.append({
                "id": idx,
                "name": prompt_3d,
                "description": item.get("description", ""),
                "visual_data": vision_data,
                "spatial_data": spatial_data
            })
            prompts_to_generate.append(prompt_3d)

        # --- NODE 4: Generating 3D Models in Parallel ---
        print(f"➡️ Menjalankan Node 4: Generating {len(prompts_to_generate)} 3D Models secara PARALEL...")
        meshy_results = await generate_multiple_models(prompts_to_generate)

        # Menggabungkan hasil Meshy kembali ke processed_components
        final_assets = []
        for i, res in enumerate(meshy_results):
            comp = processed_components[i]
            
            if isinstance(res, Exception):
                print(f"❌ Error rendering {comp['name']}: {res}")
                model_url = None
            else:
                model_url = res.get("model_url")
                
            final_assets.append({
                "asset_id": comp["id"],
                "name": comp["name"],
                "description": comp["description"],
                "model_url": model_url,
                "spatial_data": comp["spatial_data"],
                "vision_detection": comp["visual_data"]
            })

        # --- SEMUA HASIL ---
        return {
            "status": "success",
            "project_context": {
                "concept": analysis_result.get("green_solution", {}).get("concept_name", "Eco Design"),
                "gemini_full_report": analysis_result
            },
            "assets": final_assets
        }

    except Exception as e:
        print(f"❌ Error di Router: {e}")
        raise HTTPException(status_code=500, detail=str(e))