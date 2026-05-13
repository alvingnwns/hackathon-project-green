import os
import io
import json
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()

# Konfigurasi Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

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
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Format harus JPG/PNG")

    try:
        # Baca image untuk dikirim ke Gemini
        img_bytes = await file.read()
        img = Image.open(io.BytesIO(img_bytes))

        # Prompt untuk Node 1 (Analysis & Designing)
        prompt = """
        Bertindaklah sebagai arsitek lanskap permakultur. 
        Analisis gambar bangunan/lahan terbengkalai ini dan buatkan rencana transformasi menjadi taman produktif.
        
        Berikan output dalam format JSON murni dengan struktur berikut:
        {
          "design_description": "penjelasan singkat konsep taman baru",
          "visual_prompt": "prompt detail untuk generator gambar (stable diffusion) agar menghasilkan desain baru",
          "components": [
            {"id": 1, "label": "objek 3D 1", "description": "misal: wooden gazebo"},
            {"id": 2, "label": "objek 3D 2", "description": "misal: gabion planter bed"}
          ]
        }
        Batasi komponen maksimal 5 objek paling menonjol.
        """

        # Panggil Gemini
        response = model.generate_content([prompt, img])
        
        # Parsing hasil JSON dari Gemini
        # (Menghapus markdown ```json jika ada)
        clean_response = response.text.replace('```json', '').replace('```', '').strip()
        analysis_result = json.loads(clean_response)

        return {
            "status": "success",
            "analysis": analysis_result
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)