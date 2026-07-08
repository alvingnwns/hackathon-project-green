from google import genai
from google.genai import types
from core.config import settings
import time
import json

# Konfigurasi Gemini menggunakan package baru google.genai
client = genai.Client(api_key=settings.GEMINI_API_KEY)

prompt = """
        Role: Kamu adalah Environment Designer & Structural Analyst untuk proyek "Green Innovation".
        Tugas: Mentransformasi lahan/bangunan terbengkalai menjadi kawasan hijau produktif (Permakultur) dengan fokus pada minimalisasi limbah (Zero Waste) dan efisiensi biaya.

        Tugas Spesifik:
        1. Analisis Visual (Kondisi Lahan): Deteksi apakah lahan sudah berupa ekosistem hijau produktif, taman, pesawahan aktif, atau hutan.
        2. Jika lahan sudah hijau & rapi, set "is_already_green" menjadi "true", lalu berhenti (informasi lainnya boleh dikosongkan).
        3. Jika belum hijau (lahan kosong, terbengkalai, bangunan, rumput liar), lakukan analisis material bangunan (beton, kayu, besi) dan tingkat kerusakan.
        4. Keputusan Struktural: Lakukan penalaran (Reasoning) apakah bangunan lebih baik di-alihfungsikan (Retain), dihancurkan (Demolish), atau ditambah struktur hijau (Augment) berdasarkan prinsip biaya minimum dan emisi karbon terendah.
        5. Early Segmentation: Identifikasi TEPAT 5 komponen fisik utama yang perlu diubah menjadi aset 3D (1 alas lahan + 4 objek di atasnya).
        6. Hapus Penghalang: Apabila terdeteksi object lain seperti manusia, hewan, hapus saja atau abaikan.
        7. Komponen Alas Wajib: Untuk `components_for_3d`, komponen PERTAMA (id: 1) WAJIB berupa pijakan dasar/landscape. PENTING: Deskripsikan alas ini sebagai permukaan yang benar-benar datar ("flat surface"), dan tegaskan bahwa rumput atau bebatuan HARUS berupa gambar tekstur saja ("2D texture only, no 3D grass geometry popping out", "completely flat geometry"). Ini krusial agar bounding box tidak menonjol. Skala objek ini WAJIB di-fix di [8.0, 0.5, 8.0] (contoh: "Flat permaculture soil base with painted 2D green grass texture").
        8. KRITIKAL UNTUK 3D GENERATOR (TRELLIS): TRELLIS membutuhkan gambar input yang SANGAT BERSIH. Objek HARUS SATU SAJA, berada di TENGAH FRAME, dan TIDAK ADA OBJEK LAIN. Background WAJIB PUTIH POLOS (#FFFFFF). Objek yang terlalu tipis atau berongga (gazebo, pagar, kaca transparan) akan sulit direkonstruksi. KAMU WAJIB HANYA MEMBUAT OBJEK PADAT (SOLID/CHUNKY). Contoh yang BOLEH: "Solid stone raised planter box", "Closed wooden shed", "Solid water barrel", "Chunky compost bin", "Solid brick oven". Contoh yang DILARANG: "Gazebo", "Greenhouse", "Trellis", "Fences", "Thin poles".
        9. Proportional Scaling Reasoning (WAJIB): Field `scale_3d` adalah KRITIS dan HARUS ada di setiap elemen `components_for_3d`. Lakukan penalaran bertahap: (a) Buat daftar semua objek dan ukuran fisiknya di dunia nyata. (b) Bangunan Utama/Solid Shed WAJIB [3.0~4.0, 2.5~3.0, 3.0~4.0]. Objek Menengah (Tangki Air) [1.2~2.0, 1.2~2.0, 1.2~2.0]. Objek Kecil (Tempat Sampah, Bak Tanam) [0.5~1.0, 0.5~1.0, 0.5~1.0]. 

        Rules & Constraints:
        - Fokus pada "Low-Cost, High-Impact", gunakan puing bangunan jika ada untuk membuat bak tanam (raised beds) atau jalan setapak.
        - Output HARUS selalu dalam format JSON agar dapat diproses oleh pipeline automated.
        - WAJIB menghasilkan tepat 5 objek (termasuk alas).

        Output Structure (JSON & MUST BE IN ENGLISH):
        {
        "is_already_green": true/false,
        "rejection_reason": "Jika is_already_green bernilai true, tuliskan pesan edukasi pendek (bahasa Indonesia) bahwa gambar sudah berupa ekosistem hijau yang rapi sehingga tidak perlu diproses AI. Jika false, kosongkan.",
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
            "sd_xl_prompt": "Prompt DALAM BAHASA INGGRIS untuk Stable Diffusion XL. ATURAN WAJIB: (1) HANYA 1 OBJEK TUNGGAL di tengah frame, (2) background PUTIH BERSIH (#FFFFFF), (3) TIDAK ADA objek tambahan, bayangan, lantai, atau dekorasi, (4) sudut pandang isometric/3-quarter view, (5) gaya 'product photography studio render'. Contoh format: 'A single solid wooden compost bin, centered, isometric view, studio product photography, pure white background, isolated object, no shadows, no floor'. PENTING: Kualitas output 3D (TRELLIS) SANGAT BERGANTUNG pada kebersihan gambar ini.",
            "target_area": "deskripsikan MATERIAL FISIK asli di foto yang akan ditimpa dalam BAHASA INGGRIS (contoh: 'dirt ground')",
            "position_hint": "Tentukan posisi GRID 3x3: 'top-left', 'top-center', 'top-right', 'center-left', 'center', 'center-right', 'bottom-left', 'bottom-center', 'bottom-right'. PENTING: TATA LETAK HARUS RAPI DAN LOGIS layaknya Arsitek (contoh: jalan ditaruh di bottom-center tembus ke center, gazebo di center, pohon di left dan right). JANGAN menaruh 2 objek di grid yang sama untuk menghindari tabrakan 3D.",
            "scale_3d": [1.0, 1.0, 1.0],
            "relative_position": [X, Y, Z] relatif terhadap pusat lahan dengan bantuan AI reasoning. Tapi pastikan naik-turunnya (Y) object sesuai pada lahan yang dibuat.
            "scale_reasoning": "Jelaskan hierarki ukuran objek ini di dunia nyata dibandingkan objek lain dalam daftar (misal: 'Tong sampah ini ukurannya sekitar 1/4 dari ukuran gazebo')."
            }
        ]
        }
        """

def analyze_landscape(image, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "", 1)

            if raw_text.endswith("```"):
                raw_text = raw_text[: -3]
            
            # Verifikasi JSON valid
            json.loads(raw_text)
                
            return raw_text.strip()
        except Exception as e:
            error_str = str(e)
            if "503" in error_str and attempt < max_retries - 1:
                print(f"⚠️ Server Gemini sibuk (503). Mencoba lagi dalam 5 detik... (Percobaan {attempt + 1}/{max_retries})")
                time.sleep(5)
            elif "429" in error_str and attempt < max_retries - 1:
                print(f"⚠️ Server Gemini Rate Limit (429). Mencoba lagi dalam 15 detik... (Percobaan {attempt + 1}/{max_retries})")
                time.sleep(15)
            elif attempt == max_retries - 1:
                raise e
            else:
                print(f"⚠️ Error parsing JSON dari Gemini: {error_str}. Retrying...")
                time.sleep(2)