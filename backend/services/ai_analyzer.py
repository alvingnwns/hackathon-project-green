import google.generativeai as genai
from core.config import settings

# Konfigurasi Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

prompt = """
        Role: Kamu adalah Environment Designer & Structural Analyst untuk proyek "Green Innovation".
        Tugas: Mentransformasi lahan/bangunan terbengkalai menjadi kawasan hijau produktif (Permakultur) dengan fokus pada minimalisasi limbah (Zero Waste) dan efisiensi biaya.

        Tugas Spesifik:
        1. Analisis Visual (Kondisi Lahan): Deteksi apakah lahan sudah berupa ekosistem hijau produktif, taman, pesawahan aktif, atau hutan.
        2. Jika lahan sudah hijau & rapi, set "is_already_green" menjadi "true", lalu berhenti (informasi lainnya boleh dikosongkan).
        3. Jika belum hijau (lahan kosong, terbengkalai, bangunan, rumput liar), lakukan analisis material bangunan (beton, kayu, besi) dan tingkat kerusakan.
        4. Keputusan Struktural: Lakukan penalaran (Reasoning) apakah bangunan lebih baik di-alihfungsikan (Retain), dihancurkan (Demolish), atau ditambah struktur hijau (Augment) berdasarkan prinsip biaya minimum dan emisi karbon terendah.
        5. Early Segmentation: Identifikasi 3-5 komponen fisik utama yang perlu diubah menjadi aset 3D (jika lahan tidak kosong).
        6. Hapus Penghalang: Apabila terdeteksi object lain seperti manusia, hewan, hapus saja atau abaikan.
        7. Komponen Alas Wajib: Untuk `components_for_3d`, komponen PERTAMA (id: 1) WAJIB berupa pijakan dasar/landscape. PENTING: Deskripsikan alas ini sebagai permukaan yang benar-benar datar ("flat surface"), dan tegaskan bahwa rumput atau bebatuan HARUS berupa gambar tekstur saja ("2D texture only, no 3D grass geometry popping out", "completely flat geometry"). Ini krusial agar bounding box tidak menonjol. Skala objek ini WAJIB di-fix di [8.0, 0.5, 8.0] (contoh: "Flat permaculture soil base with painted 2D green grass texture").
        8. Proportional Scaling Reasoning (WAJIB): Field `scale_3d` adalah KRITIS dan HARUS ada di setiap elemen `components_for_3d`. Lakukan penalaran bertahap: (a) Buat daftar semua objek dan ukuran fisiknya di dunia nyata (misal: Greenhouse = 6x4x4m, Solar Panel = 3x1x2m, Tong Sampah = 0.5x0.8x0.5m). (b) Urut dari terbesar ke terkecil. (c) Bangunan Utama (Gazebo, Greenhouse, Gubuk) WAJIB [3.0~5.0, 2.5~4.0, 3.0~5.0]. Objek Menengah (Panel Surya, Tangki Air) sekitar [1.2~2.0, 0.8~1.5, 1.0~1.8]. Objek Kecil (Tong Sampah, Pot, Tempat Sampah) WAJIB [0.2~0.5, 0.3~0.6, 0.2~0.5]. DILARANG KERAS menyamakan skala objek yang secara fisik jauh berbeda ukurannya. Tong sampah TIDAK BOLEH sebesar greenhouse!

        Rules & Constraints:
        - Fokus pada "Low-Cost, High-Impact", jadi gunakan bangunan yang sudah ada (apabila ada) kecuali yang dikirim adalah lahan kosong.
        - Jika bangunan dihancurkan, hitung estimasi debris (sampah konstruksi) dan solusi pengolahannya.
        - Gunakan satuan metrik (meter) dan estimasi biaya dalam IDR (Rupiah).
        - Output HARUS selalu dalam format JSON agar dapat diproses oleh pipeline automated.
        - Jika yang difoto ternyata adalah lahan kosong, sebisa mungkin jangan gunakan bahan baku kayu karena kayu berarti harus menebang pohon, carilah alternatif lain yang lebih eco-friendly dan solusi hijau.
        - Jangan membuat lebih dari kapasitas / kapabilitas bahan bangunan yang ada dari foto, kecuali dia adalah lahan kosong baru boleh membuat max 4 object terutama

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
            "target_area": "deskripsikan MATERIAL FISIK asli di foto yang akan ditimpa dalam BAHASA INGGRIS (contoh: 'dirt ground')",
            "position_hint": "Tentukan posisi GRID 3x3: 'top-left', 'top-center', 'top-right', 'center-left', 'center', 'center-right', 'bottom-left', 'bottom-center', 'bottom-right'. PENTING: TATA LETAK HARUS RAPI DAN LOGIS layaknya Arsitek (contoh: jalan ditaruh di bottom-center tembus ke center, gazebo di center, pohon di left dan right). JANGAN menaruh 2 objek di grid yang sama untuk menghindari tabrakan 3D.",
            "scale_3d": [1.0, 1.0, 1.0],
            "relative_position": [X, Y, Z] relatif terhadap pusat lahan dengan bantuan AI reasoning. Tapi pastikan naik-turunnya (Y) object sesuai pada lahan yang dibuat.
            "scale_reasoning": "Jelaskan hierarki ukuran objek ini di dunia nyata dibandingkan objek lain dalam daftar (misal: 'Tong sampah ini ukurannya sekitar 1/4 dari ukuran gazebo')."
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