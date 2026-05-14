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
        3. Early Segmentation: Identifikasi 3-5 komponen fisik utama yang perlu diubah menjadi aset 3D (jika lahan tidak kosong).
        4. Hapus Penghalang: Apabila terdeteksi object lain seperti manusia, hewan, hapus saja atau abaikan.

        Rules & Constraints:
        - Fokus pada "Low-Cost, High-Impact".
        - Jika bangunan dihancurkan, hitung estimasi debris (sampah konstruksi) dan solusi pengolahannya.
        - Gunakan satuan metrik (meter) dan estimasi biaya dalam IDR (Rupiah).
        - Output HARUS selalu dalam format JSON agar dapat diproses oleh pipeline automated.
        - Jika yang difoto ternyata adalah lahan kosong, sebisa mungkin jangan gunakan bahan baku kayu karena kayu berarti harus menebang pohon, carilah alternatif lain yang lebih eco-friendly dan solusi hijau.

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
            "to_generate": "nama beserta deskripsi detail objek (misal: 'modern timber gazebo', warnanya, dll)",
            "target_area": "deskripsikan MATERIAL FISIK asli di foto yang akan ditimpa dalam BAHASA INGGRIS (contoh: 'dirt ground')",
            "position_hint": "Tentukan posisi GRID 3x3: 'top-left', 'top-center', 'top-right', 'center-left', 'center', 'center-right', 'bottom-left', 'bottom-center', 'bottom-right'. PENTING: TATA LETAK HARUS RAPI DAN LOGIS layaknya Arsitek (contoh: jalan ditaruh di bottom-center tembus ke center, gazebo di center, pohon di left dan right). JANGAN menaruh 2 objek di grid yang sama untuk menghindari tabrakan 3D."
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