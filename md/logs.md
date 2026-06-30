# 📋 LOGS — GreenScape AI Pipeline

> Dokumen ini mencatat **semua perubahan kode signifikan** yang terjadi sepanjang proyek, diurutkan dari yang terbaru ke yang terlama.
> Format: `[TANGGAL] [PHASE] — Judul Perubahan`

---

## Format Entri Log

```
### [YYYY-MM-DD] [PHASE X] — Judul Singkat
- **File:** nama_file.py
- **Perubahan:** Apa yang diubah/ditambahkan/dihapus
- **Alasan:** Mengapa perubahan ini dilakukan
- **Status:** ✅ Selesai | 🔄 Ongoing | ❌ Rollback
```

---

## 📅 2026-06-30

### [2026-06-30] [PHASE 2] — Verifikasi Split Routing + Fix Storage↔DB Linking
- **File:** `backend/services/supabase_engine.py`, `backend/api/router.py`
- **Perubahan / Hasil Verifikasi:**
  - ✅ Bucket `raw_images` dan `glb_models` keduanya sudah ada di Supabase Storage
  - ✅ `upload_raw_image()` berhasil upload dan mengembalikan public URL
  - ✅ Tabel `projects` ada di Supabase DB dengan kolom: `id`, `created_at`, `concept_name`, `estimated_cost`, `raw_json`
  - ✅ `save_project_to_db()` berhasil insert dan mengembalikan row dengan ID
  - 🔧 **FIX:** `raw_image_url` sebelumnya hanya disimpan di in-memory `_task_store`, tidak di DB
  - 🔧 **FIX:** Update signature `save_project_to_db(payload, raw_image_url=None)` — URL di-embed ke dalam `raw_json` tanpa perlu ALTER TABLE
  - 🔧 **FIX:** `router.py` line 268 → pass `raw_image_url` dari `_task_store` ke DB save
  - ✅ **Linking VERIFIED:** `raw_image_url` tersimpan di `raw_json` dan bisa di-fetch kembali via `get_project_by_id()`
- **Alasan:** Memastikan Storage Branch (Blue) dan Data Branch (Red) ter-link sesuai arsitektur Phase 2
- **Status:** ✅ Selesai

### [2026-06-30] [PHASE 1] — Verifikasi & Validasi Ingestion & Routing Pipeline
- **File:** `backend/main.py`, `backend/api/router.py`, `backend/services/ai_analyzer.py`
- **Perubahan / Hasil Verifikasi:**
  - ✅ Server FastAPI (uvicorn) startup tanpa error; semua import (`fastapi`, `uvicorn`, `PIL`, `google.genai`, `supabase`, `modal`) berhasil
  - ✅ Model `Depth-Anything-V2` dan `Grounding DINO` berhasil dimuat ke **GPU (CUDA)**
  - ✅ Endpoint `POST /api/v1/process-landscape?dry_run=true` mengembalikan **HTTP 202** + `task_id` yang valid
  - ✅ `gemini-3-flash-preview` dapat diakses dan menghasilkan output JSON yang valid
  - ✅ Logic retry 503 bekerja: Gemini sempat 503 lalu berhasil pada percobaan ke-2
  - ✅ **Gatekeeper logic** benar: gambar sawah hijau → `is_already_green: True`; gambar bangunan industri → `is_already_green: False` dengan 4 komponen teridentifikasi
  - ✅ Komponen ID 1 (base floor) menggunakan scale `[8.0, 0.5, 8.0]` sesuai aturan prompt
- **Alasan:** Verifikasi baseline bahwa seluruh Phase 1 pipeline berjalan di environment lokal
- **Status:** ✅ Selesai

### [2026-06-30] [SETUP] — Restrukturisasi Dokumentasi Proyek
- **File:** `md/logs.md`, `md/errors.md`, `md/task.md` (baru)
- **Perubahan:** Merombak `logs.md` menjadi format terstruktur dengan timestamp, phase tag, dan status. Membuat `task.md` berisi breakdown task per phase dari `newDesign.md`.
- **Alasan:** Mempersiapkan workflow pengerjaan yang rapi dan traceable sesuai arsitektur baru di `newDesign.md`.
- **Status:** ✅ Selesai

---

## 📅 2026-05-14 (Versi Lama — Arsitektur Meshy)

### [2026-05-14] [LEGACY] — Pengikatan Model 3D Aktual ke React-Three-Fiber
- **File:** `frontend/src/App.jsx`
- **Perubahan:**
  - Menghapus placeholder kubus hijau statis.
  - Membuat sub-komponen `<GLTFModel />` menggunakan `useGLTF` dari `@react-three/drei`.
  - Melakukan mapping array `resultData.assets` dan menyalurkan koordinat X, Y, Z dari Depth Engine backend ke atribut `position={[x, y, z]}`.
  - Menambahkan `Suspense` untuk handling async loading aset 3D berat dari `three.js`.
- **Status:** ✅ Selesai (Arsitektur Lama)

### [2026-05-14] [LEGACY] — Setup Frontend React + Dependensi 3D
- **File:** `frontend/` (scaffolding baru)
- **Perubahan:**
  - Membuat branch `frontend` untuk memisahkan fokus pengembangan UI.
  - Men-scaffolding React App menggunakan Vite.
  - Menginstal dependensi utama: `three`, `@react-three/fiber`, `@react-three/drei`, `axios`.
- **Status:** ✅ Selesai (Arsitektur Lama)

### [2026-05-14] [LEGACY] — Peningkatan Vision Engine & Position Hint
- **File:** `backend/services/vision_engine.py`
- **Perubahan:**
  - Memasukkan pustaka `random`.
  - Fungsi `find_target_object` mengekstrak parameter tambahan `position_hint` dari Gemini (left, right, bottom, back, middle).
  - Koordinat `u` dan `v` tidak lagi dihitung hardcode di tengah bounding box; AI menghitung luasan sekunder lalu menggunakan `random.uniform()` untuk memberikan varian koordinat natural.
- **Status:** ✅ Selesai (Arsitektur Lama)

### [2026-05-14] [LEGACY] — Iterasi Multi-Komponen di Router
- **File:** `backend/api/router.py`
- **Perubahan:**
  - Menghapus hardcode `components[0]` dan menggantinya dengan iterasi `for` untuk memproses seluruh array `components_for_3d`.
  - Router mengeksekusi Vision Engine dan Spatial Mapping secara berurutan untuk setiap komponen.
  - Mengumpulkan semua prompts dan mengirimkan ke `generate_multiple_models` secara asynchronous paralel.
  - Mengubah struktur respons JSON akhir di `/process-landscape` menjadi format `assets` array.
  - Meneruskan variabel `position_hint` dari iterasi di `router.py`.
- **Status:** ✅ Selesai (Arsitektur Lama)

---

*Log ini akan terus diperbarui setiap kali ada perubahan kode signifikan.*
