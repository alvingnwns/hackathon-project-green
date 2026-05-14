# Logs

Dokumen ini berisi log penciptaan atau perubahan kode utama yang dilakukan sepanjang proyek.

## [14 Mei 2026] - Pengikatan Model 3D Aktual ke React-Three-Fiber
- Mengubah `App.jsx` untuk tidak menggunakan *placeholder* kubus hijau lagi.
- Membuat sub-komponen `<GLTFModel />` yang menggunakan `useGLTF` (`@react-three/drei`) untuk memuat tautan `.glb` Meshy dari JSON yang sudah dikonversi secara real-time.
- Melakukan pemetaan (*mapping*) array `resultData.assets` dan menyalurkan perhitungan absolut X, Y, Z meter dari *Depth Engine* backend agar dapat dibaca di atribut `position={[x, y, z]}` properti 3D-nya.
- Menambahkan `Suspense` pada React agar React dapat mengatasi fitur asinkronus (loading aset 3D yang sangat berat) dari `three.js`.
- Membuat branch `frontend` untuk memisahkan fokus pengembangan UI tanpa merusak backend.
- Men- *scaffolding* React App menggunakan Vite.
- Menginstal dependensi utama 3D: `three`, `@react-three/fiber`, `@react-three/drei`.
- Menginstal `axios` untuk HTTP request ke backend FastAPI.
- Memasukkan pustaka logika `random` pada `vision_engine.py`.
- Fungsi `find_target_object` sekarang mengekstrak param tambahan yaitu `position_hint` dari Gemini (left, right, bottom, back, middle).
- Koordinat `u` dan `v` tak lagi dihitung *hardcode* tepat di tengah *bounding box*. AI menghitung luasan sekunder (misal di sisi kiri *box*) lalu menggunakan `random.uniform()` untuk memberikan varian pergeseran nilai koordinat natural, sehingga model 3D yang direkomendasikan tidak akan pernah saling menimpa dalam satu tempat.
- Meneruskan variabel `position_hint` dari iterasi di `router.py`.


- Menghapus *hardcode* `components[0]` dan menggantinya dengan iterasi `for` untuk memproses seluruh array `components_for_3d` yang didapat dari Gemini.
- Untuk setiap komponen, router sekarang mengeksekusi Vision Engine (deteksi sub-area) dan Spatial Mapping secara berurutan untuk mendapatkan koordinat dan *depth* unik tiap aset.
- Mengumpulkan semua *prompts* dan mengirimkannya ke `generate_multiple_models` (`await` dari Meshy Engine) secara *asynchronous* paralel.
- Mengubah struktur respons JSON akhir di `/process-landscape` menjadi format `assets` *array*, yang jauh lebih siap untuk di- *looping* pada Frontend (ThreeJS).
