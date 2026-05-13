import os
import io
import json
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
from pillow_heif import register_heif_opener

load_dotenv()
register_heif_opener()

# Konfigurasi Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3-flash-preview')

app = FastAPI()

# CORS tetap sama seperti kemarin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/process-landscape")
async def process_landscape(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/heic", "image/heif"]:
        raise HTTPException(status_code=400, detail="Format file tidak didukung.")

    try:
        # Baca image untuk dikirim ke Gemini
        img_bytes = await file.read()
        img = Image.open(io.BytesIO(img_bytes))

        # Prompt untuk Node 1 (Analysis & Designing)
        prompt = """
        Role: Kamu adalah Environment Designer & Structural Analyst untuk proyek "Green Innovation".
        Tugas: Mentransformasi lahan/bangunan terbengkalai menjadi kawasan hijau produktif (Permakultur) dengan fokus pada minimalisasi limbah (Zero Waste) dan efisiensi biaya.

        Tugas Spesifik:
        1. Analisis Visual: Deteksi material bangunan (beton, kayu, besi), tingkat kerusakan, dan potensi biodiversitas.
        2. Keputusan Struktural: Lakukan penalaran (Reasoning) apakah bangunan lebih baik di-alihfungsikan (Retain), dihancurkan (Demolish), atau ditambah struktur hijau (Augment) berdasarkan prinsip biaya minimum dan emisi karbon terendah.
        3. Early Segmentation: Identifikasi 3-5 komponen fisik utama yang perlu diubah menjadi aset 3D.

        Rules & Constraints:
        - Fokus pada "Low-Cost, High-Impact".
        - Jika bangunan dihancurkan, hitung estimasi debris (sampah konstruksi) dan solusi pengolahannya.
        - Gunakan satuan metrik (meter) dan estimasi biaya dalam IDR (Rupiah).
        - Output HARUS selalu dalam format JSON agar dapat diproses oleh pipeline automated.

        Output Structure (JSON):
        {
        "analysis": {
            "land_size_est": "string",
            "building_condition": "string",
            "structural_decision": "Retain/Demolish/Augment",
            "reasoning": "penjelasan logis keputusan tersebut"
        },
        "green_solution": {
            "concept_name": "string",
            "description": "string",
            "estimated_cost": "number (dalam IDR)",
            "waste_management": "rencana pengolahan debris"
        },
        "image_gen_prompt": "Prompt detail untuk generator gambar (landscape view, photorealistic, permaculture style)",
        "components_for_3d": [
            {
            "id": 1,
            "label": "deskripsi singkat objek (misal: 'modern timber gazebo')",
            "position_hint": "atas/tengah/bawah/kiri/kanan"
            }
        ]
        }
        """

        # Panggil Gemini
        response = model.generate_content(
            [prompt, img],
            generation_config={"response_mime_type": "application/json"}
            )
        
        # Parsing hasil JSON dari Gemini
        analysis_result = json.loads(response.text)

        return {
            "status": "success",
            "analysis": analysis_result
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)