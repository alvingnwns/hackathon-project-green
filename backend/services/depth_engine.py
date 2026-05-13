import numpy as np
from transformers import pipeline

print("⏳ Memuat model Depth-Anything-V2...")
depth_estimator = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
print("✅ Model Depth-Anything-V2 siap!")

def extract_center_depth(image):
    # Proses estimasi
    depth_result = depth_estimator(image)
    depth_array = np.array(depth_result["depth"])
    
    # Kalkulasi titik tengah
    height, width = depth_array.shape
    center_y, center_x = height // 2, width // 2
    center_z_value = int(depth_array[center_y, center_x])
    
    return {
        "image_resolution": f"{width}x{height}",
        "center_coordinate": {"u": center_x, "v": center_y},
        "center_depth_Z": center_z_value
    }