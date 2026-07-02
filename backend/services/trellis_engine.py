"""
TRELLIS Engine — Local Image-to-3D Inference Engine.
Optimized for 8GB VRAM environments (RTX 4060).
"""
import io
import os
import gc
import asyncio
from typing import Optional
from PIL import Image

try:
    import torch
    from trellis.pipelines import TrellisImageTo3DPipeline
    from trellis.utils import render_utils, postprocessing_utils
except ImportError:
    print("⚠️ TRELLIS is not installed. Please install it to use trellis_engine.py")

# Singleton pipeline
_pipeline = None

def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        print("🚀 Loading TRELLIS Image-to-3D model into VRAM (FP16)...")
        # Load in FP16 to respect 8GB VRAM limit
        _pipeline = TrellisImageTo3DPipeline.from_pretrained(
            "JeffreyXiang/TRELLIS-image-large"
        )
        _pipeline.cuda()
        
        # [MEMORY OPTIMIZATION] Attempt CPU offload if the pipeline supports it
        if hasattr(_pipeline, "enable_model_cpu_offload"):
            _pipeline.enable_model_cpu_offload()
            
        print("✅ TRELLIS loaded successfully.")
    return _pipeline

def _run_trellis_sync(img_bytes: bytes) -> bytes:
    """
    Synchronous wrapper to run TRELLIS on a single image.
    This must be run inside asyncio.to_thread to avoid blocking the event loop.
    """
    try:
        pipeline = _get_pipeline()
        
        # 1. Prepare image
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        
        # 2. Run Inference
        # [MEMORY OPTIMIZATION] Run in inference mode to save gradient VRAM
        with torch.inference_mode():
            print("📐 [TRELLIS] Generating 3D asset from image...")
            outputs = pipeline.run(
                img,
                seed=42,
            )
        
        # 3. Post-process to GLB
        print("📐 [TRELLIS] Post-processing geometry...")
        # TRELLIS returns multiple outputs; we extract the mesh and simplify it
        glb = postprocessing_utils.to_glb(
            outputs['gaussian'][0],
            outputs['mesh'][0],
            simplify=0.95,          # Decimate mesh to save filesize and memory
            texture_size=1024       # Cap texture size
        )
        
        # 4. Save to bytes buffer
        # The GLB object from trimesh (which TRELLIS uses) can be exported
        buf = io.BytesIO()
        glb.export(file_obj=buf)
        buf.seek(0)
        glb_bytes = buf.read()
        print(f"✅ [TRELLIS] GLB generated locally ({len(glb_bytes) / 1024:.1f} KB).")
        
        return glb_bytes
        
    except Exception as e:
        print(f"❌ [TRELLIS] Error during generation: {e}")
        raise e
        
    finally:
        # [CRITICAL MEMORY OPTIMIZATION]
        # Force garbage collection and empty CUDA cache immediately after generation
        # to ensure the 8GB VRAM envelope is not breached when other models run.
        gc.collect()
        if 'torch' in globals() and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

async def generate_3d_local(img_bytes: bytes) -> bytes:
    """
    Async wrapper for TRELLIS local inference.
    Executes on a background thread to prevent blocking FastAPI.
    """
    return await asyncio.to_thread(_run_trellis_sync, img_bytes)
