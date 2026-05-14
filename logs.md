# Logs

Dokumen ini berisi log penciptaan atau perubahan kode utama yang dilakukan sepanjang proyek.

## [14 Mei 2026] - Refaktor meshy_engine.py menjadi Asynchronous
- Mengganti pemanggilan API dari `requests` (sinkronus) menjadi `httpx` (asynchronous).
- Mendefinisikan ulang fungsi `generate_3d_model` menjadi `generate_3d_model_async` menggunakan `asyncio`.
- Menambahkan fungsi pembungkus `generate_multiple_models` yang menggunakan `asyncio.gather(*tasks)` untuk mengeksekusi multi *prompt* pembuatan 3D secara paralel demi menghemat total waktu *generation*.
- Mempertahankan fungsi `generate_3d_model` lama sebagai *fallback/wrapper* sinkronus agar iterasi endpoint saat ini tidak langsung *break*.
