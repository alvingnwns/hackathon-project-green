# ✅ TASK LIST — GreenScape AI Pipeline
> Berdasarkan arsitektur di `newDesign.md` | Diperbarui: 2026-06-30
> 
> **Role:** Senior AI & Backend System Architect  
> **Objective:** Membangun, mengkode, mendebug, dan mengoptimasi pipeline 2D-to-3D Generative AI yang lengkap dan otomatis.

---

## Legenda Status
- `[ ]` — Belum dikerjakan
- `[/]` — Sedang dikerjakan
- `[x]` — Selesai
- `[!]` — Ada error / blocked

---

## 🔵 Phase 0: Setup & Dokumentasi *(Prasyarat)*
- [x] Baca dan pahami `newDesign.md` (role, tech stack, system flow)
- [x] Rombak `md/logs.md` menjadi format terstruktur dengan timestamp & phase tag
- [x] Rombak `md/errors.md` menjadi format terstruktur
- [x] Buat `md/task.md` ini sebagai living task list

---

## 🟡 Phase 1: Ingestion & Routing *(FastAPI menerima gambar → Gemini)*

### Task 1.1 — Verifikasi Endpoint `/process-landscape`
- [x] Jalankan server FastAPI dan pastikan tidak ada import error
- [x] Test endpoint `POST /api/v1/process-landscape` dengan gambar dummy
- [x] Pastikan response 202 + `task_id` kembali dengan benar

### Task 1.2 — Verifikasi Gemini Analysis (`ai_analyzer.py`)
- [x] Konfirmasi model `gemini-3-flash-preview` masih valid dan dapat diakses
- [x] Test `analyze_landscape()` dengan gambar nyata dan cek output JSON-nya
- [x] Pastikan logic retry (max 5x, 503) berjalan dengan benar

### Task 1.3 — Validasi Gatekeeper Logic
- [x] Test dengan gambar yang "sudah hijau" → pastikan `is_already_green: true` dikembalikan
- [x] Test dengan gambar non-hijau → pastikan flow lanjut ke Phase 2

> **📌 Push ke GitHub setelah Phase 1 selesai!**

---

## 🟠 Phase 2: Split Routing — Data & Object

### Task 2.1 — Supabase Storage: Upload Raw Image (`supabase_engine.py`)
- [x] Verifikasi bucket `raw_images` ada di Supabase Dashboard
- [x] Test fungsi `upload_raw_image()` dengan gambar nyata
- [x] Pastikan public URL dikembalikan dengan benar

### Task 2.2 — Supabase Database: Simpan Metadata Gemini
- [x] Verifikasi tabel `projects` ada di Supabase Database
- [x] Test fungsi `save_project_to_db()` dengan payload dummy
- [x] Pastikan `concept_name`, `estimated_cost`, `raw_json` tersimpan

### Task 2.3 — Linking: Storage URL → Database
- [x] Pastikan `raw_image_url` di-store di `_task_store` dan bisa dikaitkan ke DB entry
- [x] Cek apakah perlu menambahkan kolom `raw_image_url` ke tabel `projects`

> **📌 Push ke Github setelah Phase 2 selesai!**

---

## 🔴 Phase 3: Image Processing & Conditional Logic

### Task 3.1 — Vision Engine (`vision_engine.py`)
- [x] Verifikasi `find_target_object()` dapat mendeteksi objek di gambar
- [x] Test dengan beberapa `target_label` dan `position_hint`
- [x] Pastikan fallback ke center image jika deteksi gagal

### Task 3.2 — Depth Engine (`depth_engine.py`)
- [x] Verifikasi `extract_depth_at_pixel()` menghasilkan data spasial yang valid
- [x] Test dengan koordinat u, v dari Vision Engine
- [x] Pastikan data `depth`, `x`, `y`, `z` ada di output

### Task 3.3 — Collision Engine (`collision_engine.py`)
- [x] Test `resolve_collisions()` dengan beberapa komponen yang tumpang tindih
- [x] Pastikan `position_hint` di-grid dengan benar (3x3 grid)
- [x] Cek tidak ada 2 objek di grid yang sama

### Task 3.4 — Conditional Logic: "Already Green?"
- [x] Konfirmasi parameter `is_already_green` dari Gemini mengalir ke gatekeeper
- [x] Test edge case: gambar setengah hijau, gambar indoor, gambar gelap

> **📌 Push ke Github setelah Phase 3 selesai!**

---

## 🟣 Phase 4: Serverless 3D Generation Pipeline (Modal.com)

### Task 4.1 — Setup & Konfigurasi Modal.com
- [ ] Verifikasi `MODAL_TOKEN_ID` dan `MODAL_TOKEN_SECRET` di `.env`
- [ ] Pastikan `modal_engine.py` dapat terkoneksi ke Modal.com API
- [ ] Test cold-start: cek berapa lama pertama kali container GPU menyala

### Task 4.2 — SD-XL Pipeline (`modal_sd_xl.py`)
- [ ] Review script deployment SD-XL 1.0 base model di Modal
- [ ] Pastikan decorator `@app.function(gpu="A100")` sudah benar
- [ ] Test generate 1 gambar dari `sd_xl_prompt` dan cek output-nya

### Task 4.3 — Stable Fast 3D / SF3D Pipeline (`modal_sf3d.py`)
- [ ] Review script SF3D di Modal
- [ ] Pastikan output berupa bytes `.glb` yang valid
- [ ] Test piping gambar SD-XL output → SF3D → `.glb` bytes

### Task 4.4 — `generate_multiple_3d()` Parallel Execution
- [ ] Test `modal_engine.generate_multiple_3d()` dengan 2-3 prompt sekaligus
- [ ] Pastikan asyncio paralel berjalan tanpa race condition
- [ ] Verifikasi semua hasil dikembalikan dalam urutan yang benar

> **📌 Push ke Github setelah Phase 4 selesai!**

---

## 🟢 Phase 5: Storage & Rendering

### Task 5.1 — Upload GLB ke Supabase Storage
- [ ] Test `upload_glb_bytes()` dengan `.glb` file nyata
- [ ] Pastikan bucket `glb_models` public dan URL dapat diakses
- [ ] Verifikasi fallback ke `static/models/` lokal jika Supabase gagal

### Task 5.2 — Update Database dengan GLB URL
- [ ] Pastikan `raw_json` di DB diupdate dengan `model_url` setelah GLB diupload
- [ ] Test endpoint `GET /api/v1/projects/{project_id}` untuk fetch result

### Task 5.3 — Frontend: Polling & 3D Rendering
- [x] Review frontend polling logic ke `GET /api/v1/tasks/{task_id}`
- [x] Pastikan React menerima `assets[]` array dan bisa merender `.glb` via Three.js
- [x] Test end-to-end: upload gambar → tunggu pipeline → 3D model tampil di browser

### Task 5.4 — End-to-End Integration Test (Dry Run)
- [x] Jalankan pipeline lengkap dengan `dry_run=true` menggunakan stock GLBs
- [x] Pastikan seluruh flow berjalan tanpa error dari Phase 1 hingga Phase 5
- [x] Dokumentasikan hasilnya di `logs.md`

> **📌 Push ke Github setelah Phase 5 selesai!**

---

## 🏁 Phase 6: Finalisasi & Polish

### Task 6.1 — Error Handling & Robustness
- [ ] Pastikan semua exception di-catch dan dicatat ke `errors.md`
- [ ] Tambahkan logging yang lebih detail di setiap service
- [ ] Test skenario failure: Gemini down, Modal timeout, Supabase error

### Task 6.2 — Performance Optimization
- [ ] Review async/await di semua titik bottleneck
- [ ] Pastikan cold-start Modal.com dioptimasi (image caching)
- [ ] Cek memory usage saat processing gambar besar

### Task 6.3 — Dokumentasi Final
- [ ] Update `README.md` dengan instruksi setup lengkap
- [ ] Pastikan semua `.env` variables terdokumentasi
- [ ] Final review semua `logs.md` dan `errors.md`

> **📌 Final push + tag release ke Github setelah Phase 6 selesai!**

---

*Task list ini akan diperbarui setiap kali ada progress atau perubahan plan.*
