"""
Main Router — GreenScape AI 2D-to-3D Pipeline.

Endpoints:
  POST /api/v1/process-landscape — Upload image, trigger async pipeline
  GET  /api/v1/tasks/{task_id}  — Poll task status & get results

Pipeline Flow (NEW):
  1. Validate & upload raw image to Supabase Storage
  2. Gemini analysis → components_for_3d[] with sd_xl_prompt
  3. Split routing: metadata → DB, raw image → Storage
  4. For each component: Vision (Grounding DINO) → Depth (Depth-Anything-V2) → Spatial Math
  5. Parallel Modal pipeline: SD-XL → SF3D for all non-base components
  6. Assembly: combine vision + depth + modal results into final JSON
  7. Save to Supabase DB, return result

Legacy dry_run mode preserved for testing without Modal credits.
"""

import io
import json
import uuid
import asyncio
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from PIL import Image
from pillow_heif import register_heif_opener

from core.config import settings
from services.ai_analyzer import analyze_landscape
from services.depth_engine import get_fov_from_exif, pixel_to_3d, depth_estimator, extract_depth_at_pixel
from services.vision_engine import find_target_object
from services.modal_engine import modal_engine, ModalPipelineError
from services.supabase_engine import (
    upload_raw_image,
    upload_generated_image,
    upload_glb_bytes,
    save_project_to_db,
    get_project_by_id,
)

import numpy as np

register_heif_opener()
router = APIRouter()

# ──────────────────────────────────────────────
# In-Memory Task Store (for async pipeline)
# ──────────────────────────────────────────────
# In production, replace with Redis or DB-backed queue.
# Key: task_id (str), Value: task state dict
_task_store: dict = {}

# Stock GLB pool used for dry_run mode
SUPABASE_PUBLIC = "https://tnfulriepkzquoafqidv.supabase.co/storage/v1/object/public/glb_models"
STOCK_MODELS = [
    f"{SUPABASE_PUBLIC}/integrated_vertical_greenhouse_fc0b529a.glb",
    f"{SUPABASE_PUBLIC}/industrial_solar_panel_array_o_8eb8e6cd.glb",
    f"{SUPABASE_PUBLIC}/set_of_three_color-coded_recyc_4debc1f8.glb",
    f"{SUPABASE_PUBLIC}/triple-compartment_recycled_pl_196d2497.glb",
    f"{SUPABASE_PUBLIC}/industrial_recycled_steel_gree_bccd392d.glb"
]
BASE_LAND_URL = f"{SUPABASE_PUBLIC}/flat_permaculture_soil_base_wi_c5e93b92.glb"


# ──────────────────────────────────────────────
# Helper: Build final asset list from processed components
# ──────────────────────────────────────────────
def _build_final_assets(
    processed_components: list,
    modal_results: list,
    dry_run: bool = False,
) -> list:
    """
    Merge vision/depth/spatial data with Modal-generated .glb URLs.
    modal_results is a parallel list matching non-base components.
    """
    final_assets = []
    modal_idx = 0  # index into modal_results (only for non-base)

    for comp in processed_components:
        is_base = comp.get("original_id") == 1 or comp.get("id") == 0

        if is_base:
            model_url = BASE_LAND_URL
            image_url = None
        else:
            if modal_idx < len(modal_results):
                res = modal_results[modal_idx]
                if res.get("error"):
                    print(f"⚠️ Modal failed for {comp['name']}: {res['error']}")
                    model_url = None
                    image_url = None
                else:
                    model_url = res.get("model_url")  # already uploaded to Supabase
                    image_url = res.get("image_url")
                modal_idx += 1
            else:
                model_url = None
                image_url = None

        final_assets.append({
            "asset_id": comp["id"],
            "name": comp["name"],
            "description": comp.get("description", ""),
            "model_url": model_url,
            "image_url": image_url,
            "scale_3d": comp.get("scale_3d", [1.0, 1.0, 1.0]),
            "relative_position": comp.get("relative_position", [0.0, 0.0, 0.0]),
            "position_hint": comp.get("position_hint", "center"),
            "spatial_data": comp.get("spatial_data", {}),
            "vision_detection": comp.get("visual_data", {}),
        })

    return final_assets


# ──────────────────────────────────────────────
# Main pipeline function (runs in background)
# ──────────────────────────────────────────────
async def _run_pipeline(task_id: str, img_bytes: bytes, dry_run: bool = False):
    """
    Execute the full 2D-to-3D pipeline asynchronously.
    Updates _task_store[task_id] with progress and final result.
    """
    try:
        _task_store[task_id]["status"] = "processing"
        _task_store[task_id]["progress"] = "Parsing image and running Gemini analysis..."

        # 1. Open image
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        width, height = img.size

        # 2. Upload raw image to Supabase (fire-and-forget)
        raw_image_url = await upload_raw_image(img_bytes, "upload")
        _task_store[task_id]["raw_image_url"] = raw_image_url

        # 3. Gemini Analysis
        _task_store[task_id]["progress"] = "Running Gemini landscape analysis..."
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            analysis_json_str = await loop.run_in_executor(pool, analyze_landscape, img)
        analysis_result = json.loads(analysis_json_str)

        # Gatekeeper check
        if analysis_result.get("is_already_green"):
            _task_store[task_id]["status"] = "completed"
            _task_store[task_id]["result"] = {
                "is_already_green": True,
                "rejection_reason": analysis_result.get(
                    "rejection_reason",
                    "Gambar sudah berupa ekosistem hijau yang rapi."
                )
            }
            _task_store[task_id]["progress"] = "Image is already green — rejected."
            return

        components = analysis_result.get("components_for_3d", [])
        if not components:
            components = [{
                "to_generate": "bamboo pavilion",
                "sd_xl_prompt": "A bamboo pavilion on clean white background, isometric view",
                "target_area": "ground",
                "description": "Fallback asset"
            }]

        # 4. Process each component: Vision → Depth → Spatial
        _task_store[task_id]["progress"] = f"Running Vision + Depth engines on {len(components)} components..."
        processed_components = []
        prompts_for_modal = []  # list of {sd_xl_prompt, name}

        for idx, item in enumerate(components):
            prompt_3d = item.get("to_generate", "building")
            sd_xl_prompt = item.get("sd_xl_prompt", prompt_3d)
            raw_target = item.get("target_area", "ground")
            position_hint = item.get("position_hint", "middle")
            original_item_id = item.get("id")

            target_label = "ground" if "LAHAN KOSONG" in raw_target.upper() else raw_target

            # Vision Engine
            with concurrent.futures.ThreadPoolExecutor() as pool:
                vision_data = await loop.run_in_executor(pool, find_target_object, img, target_label, position_hint)
            if not vision_data:
                vision_data = {
                    "label": target_label,
                    "confidence": 0.0,
                    "bounding_box": None,
                    "center_coordinate": {"u": width // 2, "v": height // 2},
                    "warning": "Object not detected, using image center fallback."
                }

            # Depth Engine
            target_u = vision_data["center_coordinate"]["u"]
            target_v = vision_data["center_coordinate"]["v"]
            with concurrent.futures.ThreadPoolExecutor() as pool:
                spatial_data = await loop.run_in_executor(pool, extract_depth_at_pixel, img, target_u, target_v)

            pc_entry = {
                "id": idx,
                "original_id": original_item_id,
                "name": prompt_3d,
                "description": item.get("description", ""),
                "visual_data": vision_data,
                "spatial_data": spatial_data,
                "scale_3d": item.get("scale_3d", [0.4, 0.4, 0.4]),
                "relative_position": item.get("relative_position", [0.0, 0.0, 0.0]),
                "position_hint": item.get("position_hint", "center"),
            }
            processed_components.append(pc_entry)

            # Queue for Modal (skip base/land)
            if original_item_id != 1 and idx != 0:
                prompts_for_modal.append({
                    "sd_xl_prompt": sd_xl_prompt,
                    "name": prompt_3d,
                })

        # 5. Run Modal pipeline for non-base components
        final_modal_results = []
        if prompts_for_modal:
            _task_store[task_id]["progress"] = (
                f"Running Modal.com SD-XL → SF3D for {len(prompts_for_modal)} components..."
            )

            if dry_run:
                # Dry run: use stock GLBs, skip Modal
                for i in range(len(prompts_for_modal)):
                    final_modal_results.append({
                        "name": prompts_for_modal[i]["name"],
                        "model_url": STOCK_MODELS[i % len(STOCK_MODELS)],
                        "error": None,
                    })
            else:
                # Real pipeline: Modal for SD-XL, Local TRELLIS for 3D
                modal_raw_results = await modal_engine.generate_multiple_images(prompts_for_modal)

                # Process each image into 3D sequentially using Modal TRELLIS
                for res in modal_raw_results:
                    if res.get("img_bytes") and not res.get("error"):
                        _task_store[task_id]["progress"] = f"TRELLIS Generating 3D for {res['name']}..."
                        
                        # Generate 3D on Modal
                        try:
                            glb_bytes = await modal_engine.generate_single_3d(res["img_bytes"])
                        except Exception as e:
                            print(f"⚠️ TRELLIS failed for {res['name']}: {e}")
                            glb_bytes = None
                            res["error"] = str(e)
                            
                        # Upload to Supabase
                        if glb_bytes:
                            glb_url = await upload_glb_bytes(res["name"], glb_bytes)
                            img_url = await upload_generated_image(res["name"], res["img_bytes"])
                            
                            if not glb_url:
                                # Fallback to local static directory
                                print("⚠️ Fallback to local storage for GLB.")
                            local_dir = os.path.join(settings.STATIC_DIR, "models")
                            os.makedirs(local_dir, exist_ok=True)
                            
                            safe_name = res["name"].replace(" ", "_").lower()
                            import uuid
                            unique_id = uuid.uuid4().hex[:8]
                            filename = f"{safe_name}_{unique_id}.glb"
                            local_path = os.path.join(local_dir, filename)
                            
                            with open(local_path, "wb") as f:
                                f.write(glb_bytes)
                            
                            glb_url = f"/static/models/{filename}"
                            
                        final_modal_results.append({
                            "name": res["name"],
                            "model_url": glb_url,
                            "image_url": img_url,
                            "error": None,
                        })
                    else:
                        final_modal_results.append({
                            "name": res["name"],
                            "model_url": None,
                            "image_url": None,
                            "error": res.get("error", "Unknown pipeline error"),
                        })

        # 6. Assemble final output
        _task_store[task_id]["progress"] = "Assembling final output..."
        final_assets = _build_final_assets(processed_components, final_modal_results, dry_run)

        response_payload = {
            "status": "success",
            "project_context": {
                "concept": analysis_result.get("green_solution", {}).get("concept_name", "Eco Design"),
                "gemini_full_report": analysis_result,
            },
            "assets": final_assets,
        }

        # 7. Save to DB
        save_project_to_db(response_payload)

        # 8. Finalize task
        _task_store[task_id]["status"] = "completed"
        _task_store[task_id]["result"] = response_payload
        _task_store[task_id]["progress"] = "Pipeline completed successfully."

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ [Pipeline Error] {e}\n{error_details}")
        _task_store[task_id]["status"] = "failed"
        _task_store[task_id]["progress"] = f"Pipeline failed: {e}"


# ──────────────────────────────────────────────
# POST /api/v1/process-landscape
# ──────────────────────────────────────────────
@router.post("/process-landscape")
async def process_landscape(
    file: UploadFile = File(...),
    dry_run: bool = Query(False, description="Skip Modal API — use stock GLBs instead"),
):
    """Upload image and start async 2D-to-3D pipeline. Returns a task_id for polling."""
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Format file tidak didukung.")

    try:
        img_bytes = await file.read()

        # Create async task
        task_id = str(uuid.uuid4())
        _task_store[task_id] = {
            "status": "queued",
            "progress": "Task queued, waiting to start...",
            "created_at": datetime.utcnow().isoformat(),
            "dry_run": dry_run,
            "result": None,
            "error": None,
            "raw_image_url": None,
        }

        # Launch pipeline in background
        asyncio.create_task(_run_pipeline(task_id, img_bytes, dry_run))

        return JSONResponse(
            status_code=202,
            content={
                "task_id": task_id,
                "status": "queued",
                "message": "Pipeline started. Poll GET /api/v1/tasks/{task_id} for results.",
            }
        )

    except Exception as e:
        print(f"❌ Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# GET /api/v1/tasks/{task_id}
# ──────────────────────────────────────────────
@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Poll task status. Returns current progress and final result when completed."""
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    response = {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "created_at": task["created_at"],
    }

    if task["status"] == "completed" and task["result"]:
        response["result"] = task["result"]
    elif task["status"] == "failed":
        response["error"] = task["error"]

    return response


# ──────────────────────────────────────────────
# GET /api/v1/projects/{project_id}
# ──────────────────────────────────────────────
@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Fetch a saved project from Supabase by its UUID."""
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


# ──────────────────────────────────────────────
# [LEGACY] GET /api/v1/process-landscape-sync
# Kept for backward compatibility
# ──────────────────────────────────────────────
@router.post("/process-landscape-sync")
async def process_landscape_sync(
    file: UploadFile = File(...),
    dry_run: bool = Query(False, description="Skip Meshy API — use stock GLBs instead"),
):
    """
    [LEGACY] Original synchronous pipeline using Meshy.
    Kept for backward compatibility. New code should use /process-landscape (async).
    """
    from services.meshy_engine import generate_multiple_models

    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Format file tidak didukung.")

    try:
        img_bytes = await file.read()
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        width, height = img.size

        print("➡️ [LEGACY] Running Gemini Analysis...")
        analysis_json_str = analyze_landscape(img)
        analysis_result = json.loads(analysis_json_str)

        if analysis_result.get("is_already_green"):
            reason = analysis_result.get("rejection_reason", "Image already green.")
            raise HTTPException(status_code=400, detail=reason)

        components = analysis_result.get("components_for_3d", [])
        processed_components = []
        prompts_to_generate = []

        for idx, item in enumerate(components):
            prompt_3d = item.get("to_generate", "building")
            raw_target = item.get("target_area", "ground")
            position_hint = item.get("position_hint", "middle")
            original_item_id = item.get("id")

            target_label = "ground" if "LAHAN KOSONG" in raw_target.upper() else raw_target

            vision_data = find_target_object(img, target_label, position_hint)
            if not vision_data:
                vision_data = {
                    "label": target_label, "confidence": 0.0, "bounding_box": None,
                    "center_coordinate": {"u": width // 2, "v": height // 2},
                    "warning": "Fallback to center."
                }

            target_u = vision_data["center_coordinate"]["u"]
            target_v = vision_data["center_coordinate"]["v"]
            spatial_data = extract_depth_at_pixel(img, target_u, target_v)

            pc_index = len(processed_components)
            processed_components.append({
                "id": idx, "original_id": original_item_id,
                "name": prompt_3d, "description": item.get("description", ""),
                "visual_data": vision_data, "spatial_data": spatial_data,
                "scale_3d": item.get("scale_3d", [0.4, 0.4, 0.4]),
                "position_hint": item.get("position_hint", "center"),
            })

            if original_item_id == 1 or idx == 0:
                continue
            prompts_to_generate.append(prompt_3d)

        print(f"➡️ [LEGACY] Generating {len(prompts_to_generate)} 3D models via Meshy...")
        meshy_results = []
        if prompts_to_generate:
            if dry_run:
                meshy_results = [
                    {"model_url": STOCK_MODELS[i % len(STOCK_MODELS)]}
                    for i in range(len(prompts_to_generate))
                ]
            else:
                meshy_results = await generate_multiple_models(prompts_to_generate)

        final_assets = []
        meshy_idx = 0
        for comp in processed_components:
            if comp.get("original_id") == 1 or comp.get("id") == 0:
                final_url = BASE_LAND_URL
            else:
                if meshy_idx < len(meshy_results):
                    res = meshy_results[meshy_idx]
                    if isinstance(res, Exception) or res is None:
                        final_url = None
                    else:
                        model_url = res.get("model_url")
                        if model_url:
                            from services.supabase_engine import upload_meshy_to_supabase
                            final_url = model_url if dry_run else await upload_meshy_to_supabase(comp["name"], model_url)
                        else:
                            final_url = None
                    meshy_idx += 1
                else:
                    final_url = None

            final_assets.append({
                "asset_id": comp["id"], "name": comp["name"],
                "description": comp["description"], "model_url": final_url,
                "scale_3d": comp.get("scale_3d", [1.0, 1.0, 1.0]),
                "position_hint": comp.get("position_hint", "center"),
                "spatial_data": comp["spatial_data"],
                "vision_detection": comp["visual_data"],
            })

        response_payload = {
            "status": "success",
            "project_context": {
                "concept": analysis_result.get("green_solution", {}).get("concept_name", "Eco Design"),
                "gemini_full_report": analysis_result,
            },
            "assets": final_assets,
        }

        save_project_to_db(response_payload)
        return response_payload

    except Exception as e:
        print(f"❌ [LEGACY] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


