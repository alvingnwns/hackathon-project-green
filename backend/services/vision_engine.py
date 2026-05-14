import torch
import random
from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
from core.config import settings

# 1. Deteksi Hardware (GPU/CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"⏳ Memuat model Grounding DINO ke {device}...")

# 2. Inisialisasi Model Vision (Grounding DINO Tiny)
# Model ini kecil, sangat cepat, tapi sangat pintar mencari objek dari teks
model_id = "IDEA-Research/grounding-dino-tiny"
processor = AutoProcessor.from_pretrained(
    model_id,
    token=settings.HF_API_TOKEN
    )
model = AutoModelForZeroShotObjectDetection.from_pretrained(
    model_id,
    token=settings.HF_API_TOKEN
    ).to(device)

print(f"✅ Vision Engine (Grounding DINO) siap di memori lokal ({device})!")

def find_target_object(image: Image.Image, text_prompt: str, position_hint: str = "center"):
    print(f"👁️ Mencari objek '{text_prompt}' di dalam gambar (Grid Hint: {position_hint})...")
    
    # Grounding DINO mensyaratkan teks diakhiri dengan titik
    text = text_prompt.lower().strip()
    if not text.endswith("."):
        text += "."

    # 3. Proses Gambar & Teks ke Model
    inputs = processor(images=image, text=text, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)

    # 4. Ambil Bounding Box dengan tingkat keyakinan (Confidence) > 30%
    target_sizes = [image.size[::-1]] # Format: [(height, width)]
    results = processor.post_process_grounded_object_detection(
        outputs,
        inputs.input_ids,
        text_threshold=0.3,
        target_sizes=target_sizes
    )[0]

    if len(results["scores"]) == 0:
        print(f"❌ Objek '{text_prompt}' tidak ditemukan di gambar.")
        return None 

    # 5. Ekstrak Bounding Box Terbaik (Skor Tertinggi)
    best_idx = torch.argmax(results["scores"]).item()
    bbox = results["boxes"][best_idx].tolist() # [xmin, ymin, xmax, ymax]
    confidence = results["scores"][best_idx].item()

    # 6. Hitung Spasial berdasarkan Arsitektural 3x3 Grid
    xmin, ymin, xmax, ymax = bbox
    box_w = xmax - xmin
    box_h = ymax - ymin
    
    hint = position_hint.lower()
    
    # Grid X (Columns: Left 1/6, Center 3/6, Right 5/6)
    if "left" in hint:
        target_u = xmin + (box_w * (1/6))
    elif "right" in hint:
        target_u = xmin + (box_w * (5/6))
    else: # center column
        target_u = xmin + (box_w * (3/6))

    # Grid Y (Rows: Top 1/6, Center 3/6, Bottom 5/6)
    if "top" in hint or "back" in hint:
        target_v = ymin + (box_h * (1/6))
    elif "bottom" in hint or "front" in hint:
        target_v = ymin + (box_h * (5/6))
    else: # center row
        target_v = ymin + (box_h * (3/6))

    return {
        "label": text_prompt,
        "confidence": round(confidence, 2),
        "bounding_box": {
            "xmin": round(xmin),
            "ymin": round(ymin),
            "xmax": round(xmax),
            "ymax": round(ymax)
        },
        "center_coordinate": {
            "u": int(target_u),
            "v": int(target_v)
        }
    }