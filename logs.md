# Logs

Dokumen ini berisi log penciptaan atau perubahan kode utama yang dilakukan sepanjang proyek.

## [14 Mei 2026] - Refaktor vision_engine.py: Penerapan Peletakan Dinamik (Non-Statis)
- Memasukkan pustaka logika `random` pada `vision_engine.py`.
- Fungsi `find_target_object` sekarang mengekstrak param tambahan yaitu `position_hint` dari Gemini (left, right, bottom, back, middle).
- Koordinat `u` dan `v` tak lagi dihitung *hardcode* tepat di tengah *bounding box*. AI menghitung luasan sekunder (misal di sisi kiri *box*) lalu menggunakan `random.uniform()` untuk memberikan varian pergeseran nilai koordinat natural, sehingga model 3D yang direkomendasikan tidak akan pernah saling menimpa dalam satu tempat.
- Meneruskan variabel `position_hint` dari iterasi di `router.py`.


- Menghapus *hardcode* `components[0]` dan menggantinya dengan iterasi `for` untuk memproses seluruh array `components_for_3d` yang didapat dari Gemini.
- Untuk setiap komponen, router sekarang mengeksekusi Vision Engine (deteksi sub-area) dan Spatial Mapping secara berurutan untuk mendapatkan koordinat dan *depth* unik tiap aset.
- Mengumpulkan semua *prompts* dan mengirimkannya ke `generate_multiple_models` (`await` dari Meshy Engine) secara *asynchronous* paralel.
- Mengubah struktur respons JSON akhir di `/process-landscape` menjadi format `assets` *array*, yang jauh lebih siap untuk di- *looping* pada Frontend (ThreeJS).
