import google.generativeai as genai
from core.config import settings

# Konfigurasi Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

prompt = """
        Role: Kamu adalah Environment Designer & Structural Analyst untuk proyek "Green Innovation".
        Tugas: Mentransformasi lahan/bangunan terbengkalai menjadi kawasan hijau produktif (Permakultur) dengan fokus pada minimalisasi limbah (Zero Waste) dan efisiensi biaya.

        Tugas Spesifik:
        1. Analisis Visual: Deteksi material bangunan (beton, kayu, besi), tingkat kerusakan, dan potensi biodiversitas.
        2. Keputusan Struktural: Lakukan penalaran (Reasoning) apakah bangunan lebih baik di-alihfungsikan (Retain), dihancurkan (Demolish), atau ditambah struktur hijau (Augment) berdasarkan prinsip biaya minimum dan emisi karbon terendah.
        3. Early Segmentation: Identifikasi 3-5 komponen fisik utama yang perlu diubah menjadi aset 3D.
        4. Hapus Penghalang: Apabila terdeteksi object lain seperti manusia, hewan, hapus saja atau abaikan.

        Rules & Constraints:
        - Fokus pada "Low-Cost, High-Impact".
        - Jika bangunan dihancurkan, hitung estimasi debris (sampah konstruksi) dan solusi pengolahannya.
        - Gunakan satuan metrik (meter) dan estimasi biaya dalam IDR (Rupiah).
        - Output HARUS selalu dalam format JSON agar dapat diproses oleh pipeline automated.

        Output Structure (JSON & MUST BE IN ENGLISH):
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
            "to_generate": "deskripsi singkat objek (misal: 'modern timber gazebo')",
            "target_area": "deskripsikan MATERIAL FISIK asli di foto yang akan ditimpa dalam BAHASA INGGRIS (contoh: 'concrete ruins', 'dirt ground', 'dry grass', 'pavement'. Jika hanya lahan kosong, return: 'dirt ground' atau 'grass')",
            "position_hint": "atas/tengah/bawah/kiri/kanan"
            }
        ]
        }
        """

def analyze_landscape(image):
    response = model.generate_content(
        [prompt, image],
        generation_config={"response_mime_type": "application/json"}
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text.replace("```json", "", 1)

    if raw_text.endswith("```"):
        raw_text = raw_text[: -3]
    return raw_text.strip()