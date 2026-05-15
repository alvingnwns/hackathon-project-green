# Handout Proyek: 3D Permaculture AI Generator

Dokumen ini berfungsi sebagai "jangkar memori" (checkpoint) untuk AI dan Developer guna mencegah hilangnya konteks di tengah percapakan yang panjang.

## 1. Rules / Aturan Utama Sistem
- **Cost-Saving Gatekeeper:** Gemini Vision harus selalu mengecek flag `is_already_green`. Jika gambar yang diunggah sudah berupa taman/hutan hijau, backend FastAPI langsung melempar error `HTTP 400` untuk menghemat token dan resource API.
- **Mandatory Ground / Lahan:** Sistem AI Analyzer (Gemini) selalu mewajibkan aset pertama (id/index 0) berupa `base` atau tanah/lahan. Skalanya akan dipaksa (*hard-lock*) di frontend minimal sebesar `8.0 x 0.5 x 8.0` untuk mencegah tanah yang kekecilan.
- **Physics & Anti-Hovering 3D:** Semua objek 3D (GLB) dieksekusi oleh React Three Fiber (R3F). Karena origin (*pivot point*) dari model Meshy.ai berbeda-beda, kita menggunakan komponen `<Center bottom={true}>` dari `@react-three/drei` agar setiap objek secara otomatis mendeteksi *bounding-box* bawahnya dan mendarat sempurna (tidak terbang/melayang) di `GROUND_LEVEL = -2.0`. Lahan tanah menggunakan `<Center top={true}>`.
- **Database & State:** Setiap hasil generasi json (`raw_json`) harus dikirim dan diarsipkan ke tabel `projects` di Supabase untuk mencatat riwayat desain. Kita juga mendukung pemuatan via *Upload JSON File* lokal (`mockData`) di Frontend untuk testing UI tanpa tembak API.
- **Camera Focus:** Kamera 3D dikendalikan oleh fungsi `getCameraTarget()` agar selalu memutar dan berpusat (Center of Mass) di tengah klaster kumpulan model, bukan terpatri pada ruang kosong di `0,0,0`.

## 2. Terakhir Sampai Mana (Status Terkini)
- **Backend:** `main.py`, `ai_analyzer.py`, dan `router.py` sudah stabil menghasilkan JSON dinamis (`scale_3d`, `spatial_3d_coordinates`) dan melakukan proteksi lahan yang *"already green"*. Integrasi Supabase DB untuk text JSON juga telah disambung.
- **Frontend & 3D Math Engine:** Telah dilakukan perbaikan kritis di `frontend/src/App.jsx`. Kita baru saja membuang rumusan primitif penambahan koordinat manual `0.5 * height`, menggantinya dengan library komputasi *Bounding Box* (`<Center>`). Aset sudah di-build (`npm run build`). Bug "melayang" harusnya sudah tereliminasi total secara visual. 

## 3. Next Melakukan Apa (Langkah Selanjutnya)
1. **Validasi Rendering 3D Terakhir:** Memeriksa layar/browser untuk membuktikan apakah komponen `<Center>` sukses membanting seluruh aset ke titik lantai dengan presisi (tanpa ada yang mengambang/tembus).
2. **Handle Anomali Skala:** Jika perhitungan letaknya (*placement*) sudah beres, cek rasio properti skalanya (`scale`). Konfigurasi prompt di backend mungkin perlu distel lagi agar ukuran tanaman terhadap rak, atau solar panel terhadap luas tanah bisa sangat pas proporsinya di mata arsitek.
3. **Penyempurnaan Tampilan UI:** Menyediakan indikator loading/progres yang lebih ciamik dan informatif ketika integrasi pipeline sedang berjalan lambat menunggu respon AI.
4. **Error Handling 500:** Memastikan handling error FastAPI terhadap output JSON Gemini (*kadangkala JSON bisa terputus/corrupt*) agar tidak menyebabkan app lumpuh mendadak.
