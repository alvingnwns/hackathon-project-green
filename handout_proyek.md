# Dokumen Proyek: AI Landscape & Permaculture Designer

## 1. Deskripsi Proyek (Konteks & Detail)
Proyek ini adalah sebuah sistem cerdas *End-to-End* (E2E) yang dirancang untuk mentransformasi foto lahan kosong atau lahan terbengkalai menjadi sebuah cetak biru desain lanskap permakultur interaktif dalam bentuk 3D. Menargetkan inovasi hijau (Green Innovation), aplikasi ini bertindak sebagai "arsitek digital" yang tidak hanya memberikan ide desain yang ramah lingkungan, tetapi juga secara otomatis merakit model 3D dan menghitung tata letak spasialnya di dunia nyata.

Sistem ini sangat revolusioner karena menggabungkan **Generative AI** (untuk pemahaman konteks lingkungan), **Computer Vision** (untuk segmentasi visual), **Monocular Depth Estimation** (untuk pengukuran spasial), dan **Generative 3D** (untuk pembuatan aset) ke dalam satu *pipeline* arsitektur tunggal berbasis FastAPI dan React.

## 2. Alur AI Backend (Berdasarkan Diagram Arsitektur)
Berdasarkan diagram *AI Flow* yang dirancang, aliran data (*pipeline*) berjalan sebagai berikut:

**A. Fase Inisiasi & Pemahaman Konteks**
1. **User Input:** Pengguna mengunggah foto lahan ke dalam sistem.
2. **Gen AI (Analysis & Designing):** Foto diproses oleh model Generative AI (Gemini) yang bertindak sebagai arsitek lanskap. AI ini merancang transformasi lingkungan (seperti menambahkan paviliun bambu, kolam resapan, dll) dan melakukan segmentasi awal (menentukan area target di foto).

**B. Percabangan Pipeline (Parallel Processing)**
Output dari Gen AI ("New Design") dipecah menjadi dua jalur pemrosesan utama yang berjalan berdampingan:

* **Jalur Visual & Pembuatan 3D (Kiri):**
    * **Grounded-SAM by Meta:** Digunakan untuk mencari titik presisi (segmenting & cropping) dari area target yang disarankan Gen AI (misal: "area tanah kosong" atau "area rumput kering").
    * **Meshy.ai Parallel API Calls:** Deskripsi objek bangunan dari Gen AI dikirim ke Meshy.ai. Sistem akan melakukan eksekusi API secara paralel untuk men-generate hingga 5 komponen utama menjadi file 3D berformat `.glb`.
* **Jalur Spasial & Kalkulasi Kedalaman (Kanan):**
    * **Depth-Anything-V2:** AI memproses gambar yang sama untuk memetakan jarak kedalaman (Z-estimation) dari setiap piksel dalam foto monokuler.
    * **Further Projection (Kalkulasi Matematis):** Titik pusat objek ($u, v$) dari SAM dan kedalaman ($Z$) dikombinasikan dengan titik tengah gambar ($C_x, C_y$) serta estimasi *Focal Length* kamera standar ($f_x, f_y = 1000$). Menggunakan rumus proyeksi kamera lubang jarum (pinhole camera), sistem menghitung:
        * Koordinat $X$ dan $Y$ di dunia nyata.
        * $Scale Factor$ untuk menentukan seberapa besar objek 3D harus dirender berdasarkan lebar *bounding box*.

**C. Rekonsiliasi Data & Pengiriman JSON**
Kedua jalur tersebut bertemu di akhir *backend* pipeline, menghasilkan satu buah dokumen JSON yang sangat terstruktur. JSON ini berisi `asset_id`, `url` (link unduhan `.glb` dari Meshy), dan `spatial_data` (berisi koordinat $X, Y, Z$, ukuran *Scale*, dan matriks rotasi).

**D. Rendering (Frontend)**
File JSON raksasa tersebut diterima oleh *Frontend* (React & ThreeJS) yang kemudian menyusun dan me-render model 3D tepat di atas koordinat foto lahan asli.

---

## 3. Rencana Awal (Initial Tasks)
* Membangun arsitektur *micro-pipeline* di FastAPI.
* Mengintegrasikan Gemini (Gen AI) untuk mengeluarkan output JSON terstruktur mengenai rencana desain.
* Membangun sistem *Vision* untuk mencari letak objek di dalam foto.
* Mengimplementasikan AI *Depth Estimation* untuk mengubah titik 2D (piksel) menjadi jarak 3D (metrik).
* Menyambungkan sistem ke Meshy.ai untuk mencetak teks menjadi model 3D nyata.

## 4. Progress Saat Ini
* **Integrasi E2E Berhasil:** Seluruh *node* AI (Gemini -> DINO/SAM -> Depth-Anything -> Meshy) sudah berhasil dijahit dalam satu alur di `api/router.py`.
* **Matematika Spasial Tervalidasi:** Rumus proyeksi spasial untuk mendapatkan variabel X, Y, Z dan Scale sudah diimplementasikan dengan kalkulasi matriks *intrinsic camera*.
* **Optimasi 3D Generation:** Proses Meshy.ai telah dikalibrasi menggunakan pola *Hybrid Sync-Async* untuk menghindari *Timeout*, serta optimasi *prompt* untuk menjaga keseimbangan antara ukuran file `.glb` dan kualitas *texture bake* PBR.

## 5. Arah Progress Berikutnya (What's Next)
* **Parallel 3D Generation Execution:** Memodifikasi `meshy_engine.py` menggunakan `asyncio.gather` agar sistem dapat memanggil API Meshy hingga 5 objek sekaligus secara bersamaan (paralel), memangkas waktu tunggu *user* secara drastis.
* **Pengembangan Frontend (React & Vite):** Mulai menggeser fokus ke UI/UX. Membangun halaman antarmuka pengguna untuk mengunggah foto lahan.
* **ThreeJS Canvas Integration:** Mengimplementasikan logika *polling* di React untuk memuat URL `.glb` dari JSON *backend*, dan menempatkannya secara presisi ke dalam kanvas 3D berdasarkan koordinat spasial yang telah dihitung.