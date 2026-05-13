import io
import json
from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image
from pillow_heif import register_heif_opener
from core.config import settings
from services.ai_analyzer import analyze_landscape
from services.depth_engine import extract_center_depth

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

        # 2. Eksekusi Services
        analysis_json_str = analyze_landscape(img)
        analysis_result = json.loads(analysis_json_str)
        
        spatial_data = extract_center_depth(img)

        # 3. Kembalikan Response
        return {
            "status": "success",
            "analysis": analysis_result,
            "spatial_data_experiment": spatial_data
        }

    except Exception as e:
        print(f"Error di Router: {e}")
        raise HTTPException(status_code=500, detail=str(e))