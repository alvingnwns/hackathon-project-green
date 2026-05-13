import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

# 1. Deteksi Hardware (GPU/CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"⏳ Memuat model Grounding DINO ke {device}...")

# 2. Inisialisasi Model Vision (Grounding DINO Tiny)
# Model ini kecil, sangat cepat, tapi sangat pintar mencari objek dari teks
model_id = "IDEA-Research/grounding-dino-tiny"
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id).to(device)

print(f"✅ Vision Engine (Grounding DINO) siap di memori lokal ({device})!")

def find_target_object(image: Image.Image, text_prompt: str):
    print(f"👁️ Mencari objek '{text_prompt}' di dalam gambar...")
    
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
        box_threshold=0.3,
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

    # 6. Hitung Titik Tengah (u, v) dari Bounding Box tersebut
    center_u = int((bbox[0] + bbox[2]) / 2)
    center_v = int((bbox[1] + bbox[3]) / 2)

    return {
        "label": text_prompt,
        "confidence": round(confidence, 2),
        "bounding_box": {
            "xmin": round(bbox[0]),
            "ymin": round(bbox[1]),
            "xmax": round(bbox[2]),
            "ymax": round(bbox[3])
        },
        "center_coordinate": {
            "u": center_u,
            "v": center_v
        }
    }