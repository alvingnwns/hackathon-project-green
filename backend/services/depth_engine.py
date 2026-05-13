import numpy as np
import torch
from PIL import Image
from transformers import pipeline
from core.config import settings

# 1. Deteksi Hardware (GPU/CPU)
if torch.cuda.is_available():
    device = 0
    device_name = "GPU (CUDA)"
elif torch.backends.mps.is_available():
    device = "mps"
    device_name = "GPU (Apple MPS)"
else:
    device = -1
    device_name = "CPU"

print(f"⏳ Memuat model Depth-Anything-V2 ke {device_name}...")

# 2. Inisialisasi Pipeline dengan alokasi device
depth_estimator = pipeline(
    task="depth-estimation", 
    model="depth-anything/Depth-Anything-V2-Small-hf",
    device=device,
    token=settings.HF_API_TOKEN
)

print(f"✅ Model Depth-Anything-V2 siap di memori lokal ({device_name})!")

def extract_center_depth(image: Image.Image):
    print(f"🖥️ Memproses depth map menggunakan {device_name} lokal...")
    
    # Eksekusi model lokal
    depth_result = depth_estimator(image)
    
    # Hasil balikan dari pipeline adalah dictionary dengan key "depth" berupa PIL Image grayscale
    depth_map_img = depth_result["depth"]
    depth_array = np.array(depth_map_img)

    # Kalkulasi Z di titik tengah
    height, width = depth_array.shape
    center_y, center_x = height // 2, width // 2
    center_z_value = int(depth_array[center_y, center_x])

    return {
        "image_resolution": f"{width}x{height}",
        "center_coordinate": {"u": center_x, "v": center_y},
        "center_depth_Z": center_z_value,
        "source": f"Local Inference ({device_name})"
    }