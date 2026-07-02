# 🌿 GreenScape AI - Project Handout
**"Zero-Waste Permaculture 2D-to-3D Transformation"**

## 📖 Deskripsi Project
**GreenScape AI** adalah platform kecerdasan buatan end-to-end yang dirancang untuk mentransformasi foto lahan kosong, reruntuhan, atau area terbengkalai menjadi desain ekosistem hijau (Permakultur) dalam bentuk **Interactive 3D Scene**. Sistem ini menggunakan prinsip arsitektur *Zero Waste* dan efisiensi karbon, di mana puing-puing dioptimalkan menjadi sumber daya, bukan sampah.

## 🛠️ Teknologi yang Digunakan (Tech Stack)
**Frontend (Web UI & 3D Viewer):**
- **React.js & Vite:** Kerangka utama untuk UI yang interaktif dan *blazing fast*.
- **Tailwind CSS:** Styling komponen antarmuka (UI) yang modern dan responsif.
- **Three.js & React Three Fiber (@react-three/drei):** Mesin *rendering* 3D di dalam browser untuk memvisualisasikan model `.glb` lengkap dengan pencahayaan (lighting), bayangan, dan navigasi (orbit controls).

**Backend & Orkestrasi:**
- **Python & FastAPI:** Server backend asinkron berkinerja tinggi untuk mengatur alur data REST API.
- **Modal.com (Serverless GPU):** Platform komputasi awan *serverless* yang mengeksekusi kontainer GPU (Nvidia A10G) secara dinamis (tanpa biaya *idle*) dengan integrasi `remote.aio()`.
- **Supabase:** *BaaS (Backend as a Service)* yang menyediakan Database PostgreSQL untuk menyimpan metadata project (JSON) dan *Bucket Storage* untuk menyimpan gambar mentah serta aset `.glb`.

**Artificial Intelligence (AI Models & Engines):**
- **Google Gemini (gemini-3.5-flash):** *Vision-Language Model (VLM)* mutakhir yang bertugas sebagai "Arsitek Utama", menganalisis gambar, menentukan material bangunan yang bisa di-daur-ulang, dan mengeluarkan instruksi tata letak dalam format JSON.
- **Grounding DINO:** Model *Zero-Shot Object Detection* untuk mendeteksi titik pusat piksel objek target di dunia nyata dari gambar lahan 2D.
- **Depth-Anything-V2:** Model *Monocular Depth Estimation* untuk mengukur jarak relatif dan kedalaman tata ruang dari lensa kamera ke titik objek (Konversi 2D Pixel ke 3D XYZ Spatial).
- **Stable Diffusion XL (SD-XL 1.0 base):** Model *Text-to-Image* (dijalankan di Modal.com) yang membuat tekstur dan gambar *render* arsitektur dari *prompt* Gemini.
- **Stable Fast 3D (SF3D):** Model *Image-to-3D* berbasis Triplane-NeRF (dijalankan di Modal.com) yang menyulap gambar 2D dari SD-XL menjadi aset geometri 3D utuh (`.glb`) dalam waktu 0.5 detik.

## 🚀 Pencapaian Kita (Achievements)
Selama hackathon ini, kita telah berhasil membangun arsitektur kompleks yang mengintegrasikan berbagai model AI mutakhir:
1. **Vision-Language Reasoning:** Mengintegrasikan **Google Gemini (gemini-3.5-flash)** untuk bertindak sebagai Arsitek AI yang memberikan penalaran tata ruang, merumuskan 4-5 komponen desain, dan mematuhi format JSON secara ketat.
2. **Spatial Intelligence Pipeline:** Membangun *Depth & Vision Engine* lokal menggunakan **Grounding DINO** (Object Detection) dan **Depth-Anything-V2** (Depth Estimation) untuk menghitung koordinat spasial absolut (XYZ) dari gambar 2D.
3. **Serverless 3D Generation:** Menerapkan orkestrasi asinkron (Native `.aio()`) menggunakan **Modal.com** untuk memproses *prompt* teks menjadi gambar via **SD-XL**, lalu menyulapnya menjadi objek 3D (`.glb`) via **Stable Fast 3D (SF3D)** secara paralel.
4. **Cloud Storage & Frontend:** Integrasi **Supabase** untuk penyimpanan aset dinamis, dipadukan dengan **React + Three.js (@react-three/fiber)** untuk merender lingkungan 3D secara mulus di browser.

## ⚠️ Tantangan & Masalah Saat Ini
Meskipun arsitektur pipeline telah berjalan 100%, kita menghadapi keterbatasan dari sisi model 3D Generator (State of the Art AI) saat ini:
1. **Kelemahan Model SF3D pada Struktur Berongga:** SF3D menggunakan pendekatan *Triplane NeRF* yang sangat handal untuk benda padat (solid), namun akan menghasilkan bentuk "meleleh" (melted) saat diminta membuat struktur arsitektur tipis/berongga seperti tiang gazebo, pagar, atau rumah kaca.
   - *Mitigasi Saat Ini:* Melakukan *Prompt Engineering* ekstrim pada Gemini agar hanya mendesain objek padat (*solid planter box, closed shed, water barrel*).
2. **Limitasi API & Cold-Start:** Mengalami error rate-limit (429) dari Gemini Free Tier dan gRPC Timeout pada Modal.com saat *cold-start*.
   - *Mitigasi Saat Ini:* Mengganti model Gemini ke versi stabil terbaru dan menulis ulang *thread-executor* menjadi *Native Async* di Python untuk mencegah *deadlock*.

## 🔭 Rencana Kedepannya (What's Next)
1. **Migrasi Mesin 3D Khusus Arsitektur:** Di masa depan, integrasi API khusus arsitektur seperti **Meshy.ai** atau **Luma Genie** akan menggantikan SF3D untuk memungkinkan pembuatan objek kompleks seperti rumah kaca transparan atau gazebo bambu.
2. **Database Asset Caching:** Membangun perpustakaan aset pintar. Jika AI merekomendasikan "Tong Sampah Kompos" standar, sistem tidak perlu me-render ulang dari nol di GPU, melainkan mengambil dari *cache* Supabase untuk mempercepat *loading* menjadi di bawah 10 detik.
3. **Export to AR / VR:** Menambahkan tombol ekspor ke format `.usdz` agar pengguna bisa memproyeksikan lanskap langsung ke lahan nyata mereka menggunakan *Augmented Reality* (AR) di perangkat iOS/Android.

---
*Dibuat khusus untuk penjurian ORCA Hackathon.*
