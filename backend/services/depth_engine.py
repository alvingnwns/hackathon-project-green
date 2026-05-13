import io
import os
import requests
import numpy as np
from PIL import Image
from core.config import settings

# Endpoint resmi dari Hugging Face Inference API
API_URL = os.getenv("API_URL")
headers = {"Authorization": f"Bearer {settings.HF_API_TOKEN}"}

def extract_center_depth(image: Image.Image):
    # 1. Konversi gambar PIL kembali ke format byte (JPEG) untuk dikirim
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()

    # 2. Tembak API Hugging Face
    print("☁️ Mengirim gambar ke Hugging Face API untuk kalkulasi kedalaman...")
    response = requests.post(API_URL, headers=headers, data=img_bytes)

    if response.status_code != 200:
        # Menangani kasus "Cold Start" dari sisi server Hugging Face
        error_msg = response.json()
        if "estimated_time" in error_msg:
            raise Exception(f"Model Hugging Face sedang loading. Coba lagi dalam {int(error_msg['estimated_time'])} detik.")
        raise Exception(f"Hugging Face API Error: {response.text}")

    # 3. API mengembalikan gambar Depth Map dalam format binary
    depth_image = Image.open(io.BytesIO(response.content))
    depth_array = np.array(depth_image)

    # 4. Kalkulasi nilai Z di titik tengah
    height, width = depth_array.shape
    center_y, center_x = height // 2, width // 2
    center_z_value = int(depth_array[center_y, center_x])

    return {
        "image_resolution": f"{width}x{height}",
        "center_coordinate": {"u": center_x, "v": center_y},
        "center_depth_Z": center_z_value,
        "source": "Hugging Face API"
    }