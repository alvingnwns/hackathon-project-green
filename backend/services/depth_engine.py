import numpy as np
import math
import torch
from PIL import Image, ExifTags
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

def get_fov_from_exif(image: Image.Image, default_fov=70.0):
    # Mencoba mengekstrak Focal Length dari EXIF untuk menghitung FOV asli kamera.
    try:
        exif = image.getexif()
        if not exif:
            return default_fov

        # Mencari tag FocalLengthIn35mmFilm (Tag ID: 41989)
        focal_length_35mm = None
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag == 'FocalLengthIn35mmFilm':
                focal_length_35mm = float(value)
                break
        
        # Jika ketemu, hitung FOV horizontal (Asumsi sensor 35mm memiliki lebar 36mm)
        if focal_length_35mm:
            # Rumus FOV: 2 * arctan(sensor_width / (2 * focal_length))
            fov_radians = 2 * math.atan(36.0 / (2 * focal_length_35mm))
            fov_degrees = math.degrees(fov_radians)
            print(f"📸 EXIF Ditemukan! Lensa ekuivalen {focal_length_35mm}mm -> FOV: {round(fov_degrees, 2)}°")
            return fov_degrees
            
    except Exception as e:
        print(f"⚠️ Gagal membaca EXIF, menggunakan fallback FOV. Error: {e}")
        
    return default_fov

def pixel_to_3d(u, v, z_raw, width, height, fov_degrees=70):
    fov_radians = math.radians(fov_degrees)
    focal_length = (width / 2) / math.tan(fov_radians / 2)

    cx = width/2
    cy = height/2

    z_metric = 50.0 / (z_raw + 1)

    X = (u - cx) * z_metric / focal_length
    Y = (v - cy) * z_metric / focal_length

    return round(X, 2), round(Y, 2), round(z_metric, 2)

def extract_depth_at_pixel(image: Image.Image, target_u: int, target_v: int):
    """Mengekstrak Z dan kalkulasi 3D berdasarkan koordinat piksel spesifik"""
    print(f"🖥️ Memproses depth map menggunakan {device_name} lokal...")
    
    # Eksekusi model lokal
    depth_result = depth_estimator(image)
    depth_map_img = depth_result["depth"]
    depth_array = np.array(depth_map_img)

    height, width = depth_array.shape
    
    # Pengaman batas agar koordinat tidak melebihi resolusi (Out of Bounds)
    target_u = min(max(target_u, 0), width - 1)
    target_v = min(max(target_v, 0), height - 1)
    
    # Kalkulasi Z di titik target
    target_z_value = int(depth_array[target_v, target_u])

    # Ekstrak FOV Dinamis dari Gambar
    dynamic_fov = get_fov_from_exif(image)

    # Konversi ke 3D dengan FOV yang sudah disesuaikan
    X, Y, Z_metric = pixel_to_3d(target_u, target_v, target_z_value, width, height, fov_degrees=dynamic_fov)

    return {
        "image_resolution": f"{width}x{height}",
        "camera_metadata": {
            "estimated_fov_degrees": round(dynamic_fov, 2),
            "is_fallback": dynamic_fov == 70.0
        },
        "target_coordinate": {"u": target_u, "v": target_v},
        "raw_depth_Z": target_z_value,
        "spatial_3d_coordinates": {
            "X_meter": X,
            "Y_meter": Y,
            "Z_meter": Z_metric
        },
        "source": f"Local Inference ({device_name})"
    }