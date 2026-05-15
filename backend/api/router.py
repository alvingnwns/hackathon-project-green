import io
import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from PIL import Image
from pillow_heif import register_heif_opener
from core.config import settings

# Import semua engine kita
from services.ai_analyzer import analyze_landscape
from services.depth_engine import get_fov_from_exif, pixel_to_3d, depth_estimator, extract_depth_at_pixel
from services.vision_engine import find_target_object
from services.meshy_engine import generate_multiple_models
from services.supabase_engine import upload_meshy_to_supabase, save_project_to_db
import numpy as np

register_heif_opener()
router = APIRouter()

# Stock GLB pool used for dry_run mode (no Meshy credits consumed)
SUPABASE_PUBLIC = "https://tnfulriepkzquoafqidv.supabase.co/storage/v1/object/public/glb_models"
STOCK_MODELS = [
    f"{SUPABASE_PUBLIC}/integrated_vertical_greenhouse_fc0b529a.glb",
    f"{SUPABASE_PUBLIC}/industrial_solar_panel_array_o_8eb8e6cd.glb",
    f"{SUPABASE_PUBLIC}/set_of_three_color-coded_recyc_4debc1f8.glb",
]

@router.post("/process-landscape")
async def process_landscape(file: UploadFile = File(...), dry_run: bool = Query(False, description="Skip Meshy API — use stock GLBs instead")):
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
        
        # Validasi Ekosistem Hijau
        if analysis_result.get("is_already_green"):
            reason = analysis_result.get("rejection_reason", "Gambar sudah berupa ekosistem hijau yang rapi. Tidak perlu memproses 3D.")
            # Mengembalikan response tanpa perlu raise HTTPException (agar bisa dirender rapi di UI)
            # 400 Bad Request juga bisa, tapi lebih halus via 400
            raise HTTPException(status_code=400, detail=reason)
            
        # Ekstrak komponen dari saran Gemini
        components = analysis_result.get("components_for_3d", [])
        
        # Proses pipeline paralel untuk Multi-Object
        processed_components = []
        prompts_to_generate = []
        prompts_to_pc_index = []  # mapping from prompt index -> processed_components index

        # Optional: reuse a static base land model from Supabase to save Meshy credits
        BASE_LAND_URL = "https://tnfulriepkzquoafqidv.supabase.co/storage/v1/object/public/glb_models/flat_permaculture_soil_base_wi_c5e93b92.glb"

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

            # record original item id from Gemini (if present) to detect base
            original_item_id = item.get("id")
            pc_index = len(processed_components)
            processed_components.append({
                "id": idx,
                "original_id": original_item_id,
                "name": prompt_3d,
                "description": item.get("description", ""),
                "visual_data": vision_data,
                "spatial_data": spatial_data,
                "scale_3d": item.get("scale_3d", [0.4, 0.4, 0.4]), # Fallback scale default
                "position_hint": item.get("position_hint", "center") # Hint posisi grid dari Gemini
            })

            # If this component is the base/land (Gemini id == 1 or first item), DO NOT request Meshy.
            # We'll reuse the pre-uploaded Supabase GLB to save credits.
            if original_item_id == 1 or idx == 0:
                # skip adding to prompts_to_generate
                continue

            # otherwise queue for Meshy generation and map prompt->processed_components index
            prompts_to_generate.append(prompt_3d)
            prompts_to_pc_index.append(pc_index)

        # --- NODE 4: Generating 3D Models in Parallel ---
        print(f"➡️ Menjalankan Node 4: Generating {len(prompts_to_generate)} 3D Models secara PARALEL...")
        # Call Meshy only for non-base items
        meshy_results = []
        if prompts_to_generate:
            if dry_run:
                # Dry run: skip Meshy, cycle through stock GLBs
                print("🧪 [DRY RUN] Melewati Meshy API — menggunakan stock GLBs.")
                meshy_results = [
                    {"model_url": STOCK_MODELS[i % len(STOCK_MODELS)]}
                    for i in range(len(prompts_to_generate))
                ]
            else:
                meshy_results = await generate_multiple_models(prompts_to_generate)

        # map results back to processed_components using prompts_to_pc_index
        result_by_pc_index = {}
        for i, res in enumerate(meshy_results):
            pc_idx = prompts_to_pc_index[i]
            result_by_pc_index[pc_idx] = res

        # Menggabungkan semua hasil (menggunakan BASE_LAND_URL for base)
        final_assets = []
        for pc_idx, comp in enumerate(processed_components):
            # If component is base (original_id==1 or id==0), use static BASE_LAND_URL
            if comp.get("original_id") == 1 or comp.get("id") == 0:
                final_url = BASE_LAND_URL
            else:
                res = result_by_pc_index.get(pc_idx)
                if isinstance(res, Exception) or res is None:
                    print(f"❌ Error rendering {comp['name']}: {res}")
                    final_url = None
                else:
                    model_url = res.get("model_url")
                    if model_url:
                        # dry_run: stock URLs are already public, skip re-uploading
                        final_url = model_url if dry_run else await upload_meshy_to_supabase(comp["name"], model_url)
                    else:
                        final_url = None

            final_assets.append({
                "asset_id": comp["id"],
                "name": comp["name"],
                "description": comp["description"],
                "model_url": final_url,
                "scale_3d": comp.get("scale_3d", [1.0, 1.0, 1.0]),  # Skala proporsional dari Gemini reasoning
                "position_hint": comp.get("position_hint", "center"), # Hint posisi grid dari Gemini
                "spatial_data": comp["spatial_data"],
                "vision_detection": comp["visual_data"]
            })

        # --- SEMUA HASIL ---
        response_payload = {
            "status": "success",
            "project_context": {
                "concept": analysis_result.get("green_solution", {}).get("concept_name", "Eco Design"),
                "gemini_full_report": analysis_result
            },
            "assets": final_assets
        }

        # Simpan History JSON ke Supabase PostgreSQL
        save_project_to_db(response_payload)

        return response_payload

    except Exception as e:
        print(f"❌ Error di Router: {e}")
        raise HTTPException(status_code=500, detail=str(e))