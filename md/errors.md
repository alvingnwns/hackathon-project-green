# ❌ ERRORS — GreenScape AI Pipeline

> Dokumen ini mencatat **semua error yang ditemukan** selama pengembangan, lengkap dengan penyebab dan solusinya.
> Format: `[TANGGAL] [PHASE] — Nama Error`

---

## Format Entri Error

```
### [YYYY-MM-DD] [PHASE X] — Nama Error / Exception
- **File & Baris:** nama_file.py : L##
- **Pesan Error:** Teks error lengkap
- **Penyebab:** Root cause analisis
- **Solusi:** Langkah yang diambil untuk fix
- **Status:** ✅ Fixed | 🔄 In Progress | ⚠️ Workaround | ❌ Unresolved
```

---

## 📅 2026-07-02

### [2026-07-02] [PHASE 5] — httpx.ReadTimeout on Polling / API Hanging
- **File & Baris:** `backend/api/router.py`, `backend/services/supabase_engine.py`
- **Pesan Error:** `httpx.ReadTimeout` during `client.get()` in `test_e2e.py`
- **Penyebab:** Eksekusi network (Supabase I/O) dan beban CUDA (Depth-Anything, Grounding DINO) adalah proses *blocking synchronous* di dalam `async def` FastAPI. Hal ini menghalangi Event Loop `asyncio`, sehingga Uvicorn berhenti melayani request HTTP lain yang masuk (misal, request GET status/polling), menyebabkan API hang dan akhirnya client terkena Timeout.
- **Solusi:** Membungkus setiap call *blocking* dengan `loop.run_in_executor(pool, func)`. Khusus Supabase dirubah dengan `ThreadPoolExecutor` di dalam fungsinya. Mengubah parameter API Timeout di script client.
- **Status:** ✅ Fixed

## 📅 2026-06-30
### [2026-06-30] [SETUP] — ModuleNotFoundError: No module named 'fastapi'
- **File & Baris:** `backend/main.py` : L2
- **Pesan Error:** `ModuleNotFoundError: No module named 'fastapi'`
- **Penyebab:** VS Code menggunakan Python interpreter global, bukan dari virtual environment `green_venv` yang sudah terinstall FastAPI.
- **Solusi:** Arahkan VS Code ke interpreter `green_venv`: `Ctrl+Shift+P` → `Python: Select Interpreter` → pilih `.\backend\green_venv\Scripts\python.exe`.
- **Status:** ✅ Fixed
- **Referensi:** Conversation `1173a417`

---

## 📅 2026-06-20

### [2026-06-20] [PHASE 2] — Supabase Query Syntax Error
- **File & Baris:** `backend/` health check file : L21
- **Pesan Error:** Syntax error pada `.select()` method Supabase client
- **Penyebab:** Penggunaan syntax query Supabase yang salah pada health check endpoint.
- **Solusi:** Memperbaiki struktur method call `.select()` sesuai Supabase Python SDK v2.
- **Status:** ✅ Fixed
- **Referensi:** Conversation `fc76ed74`

## 📅 2026-07-07

### [2026-07-07] [PHASE 4] — nvdiffrast Build Crash: IndexError on TORCH_CUDA_ARCH_LIST
- **File & Baris:** `backend/services/modal_trellis.py` (Modal image build step)
- **Pesan Error:** `IndexError: list index out of range` at `torch/utils/cpp_extension.py:1985` — `arch_list[-1] += '+PTX'`
- **Penyebab:** Modal membangun container image di mesin **tanpa GPU**. PyTorch mencoba auto-detect arsitektur CUDA dari GPU yang terlihat, tetapi karena tidak ada GPU, `arch_list` kosong (`[]`), dan akses `arch_list[-1]` menyebabkan `IndexError`.
- **Solusi:** Menambahkan `"TORCH_CUDA_ARCH_LIST": "8.6"` di blok `.env()` Modal image **sebelum** `run_commands` yang menginstal `nvdiffrast`. Nilai `8.6` sesuai dengan arsitektur A10G (Ampere SM86).
- **Status:** ✅ Fixed

### [2026-07-07] [PHASE 4] — CUDA Version Mismatch: PyTorch cu124 vs Container cu118
- **File & Baris:** `backend/services/modal_trellis.py` (Modal image build step)
- **Pesan Error:** `RuntimeError: The detected CUDA version (11.8) mismatches the version that was used to compile PyTorch (12.4 / 13.0).`
- **Penyebab:** `pip install torch` tanpa `--index-url` mengunduh PyTorch terbaru yang dikompilasi dengan CUDA 12.x/13.x, sementara container menggunakan base image CUDA 11.8. Versi `xformers` tanpa pin juga menarik PyTorch versi terbaru sebagai dependensi, menimpa versi cu118 yang sudah dipasang.
- **Solusi:** Pin `torch==2.4.0+cu118`, `torchvision==0.19.0+cu118`, `xformers==0.0.27.post2` secara eksplisit, dan gunakan `extra_index_url="https://download.pytorch.org/whl/cu118"` di `.pip_install()`.
- **Status:** ✅ Fixed

### [2026-07-07] [PHASE 4] — TRELLIS Missing Dependencies Chain (rembg, onnxruntime, plyfile, etc.)
- **File & Baris:** `backend/services/modal_trellis.py` (Modal container runtime)
- **Pesan Error:** Serangkaian `ModuleNotFoundError` berturut-turut: `rembg` → `onnxruntime` → `plyfile` → `torch_scatter` → `flexicubes`
- **Penyebab:** Daftar dependensi `modal_trellis.py` tidak lengkap. TRELLIS memiliki banyak dependensi implisit yang tidak terdokumentasi di satu tempat. Daftar di `setup.sh --basic` juga tidak mencakup semuanya (misal `plyfile`, `flexicubes`, `torch-scatter`).
- **Solusi:** Melakukan full import scan (`grep` semua `import` di `trellis/`) untuk mendapatkan daftar komprehensif. Menambahkan **semua** modul: `rembg`, `onnxruntime`, `open3d`, `transformers`, `tqdm`, `plyfile`, `torch-scatter`, `flexicubes`, `requests`, dan `utils3d` (git commit).
- **Status:** ✅ Fixed

---

### [2026-07-08] [PHASE 4] — flexicubes Not Found on PyPI + Application Control Block
- **File & Baris:** `backend/services/modal_trellis.py` (Modal image build step)
- **Pesan Error:** `ERROR: Could not find a version that satisfies the requirement flexicubes` dan `An Application Control policy has blocked this file` (untuk `modal.exe`)
- **Penyebab:** 
  - `flexicubes` dan `torch_scatter` ditemukan di full import scan, tapi ternyata **hanya** digunakan di folder `trellis/representations/mesh/flexicubes/examples/` (contoh demo), bukan di pipeline inference. FlexiCubes sudah ter-vendor sebagai modul internal TRELLIS.
  - `modal.exe` di-block oleh Windows Application Control policy. Workaround: gunakan `python -m modal` sebagai gantinya.
- **Solusi:** Menghapus `flexicubes` dan `torch-scatter` dari `pip_install()`. Menggunakan `python -m modal deploy/run` sebagai alternatif `modal.exe`.
- **Status:** ✅ Fixed

### [2026-07-08] [PHASE 4] — utils3d Ghost Install: Empty Wheel from Git Commit
- **File & Baris:** `backend/services/modal_trellis.py` (Modal image build step)
- **Pesan Error:** `ModuleNotFoundError: No module named 'utils3d'` meskipun instalasi sebelumnya terlihat "berhasil".
- **Penyebab:** Instalasi `pip install git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e...` menghasilkan wheel kosong (`UNKNOWN-0.0.0-py3-none-any.whl`, hanya 1794 bytes). Paket metadata terpasang tetapi kode Python sebenarnya tidak termasuk. Ini menyebabkan kontainer Modal terus retry inisialisasi (berputar/cycle tanpa henti).
- **Solusi:** Mengganti instalasi dari git commit ke PyPI langsung (`"utils3d"` di `.pip_install()`), yang menyediakan wheel lengkap dan teruji.
- **Status:** ✅ Fixed

### [2026-07-08] [PHASE 4] — ROOT CAUSE: TRELLIS Git Submodule Tidak Di-clone
- **File & Baris:** `backend/services/modal_trellis.py` baris 70 (`git clone`)
- **Pesan Error:** `ModuleNotFoundError: No module named 'trellis.representations.mesh.flexicubes.flexicubes'`
- **Penyebab:** TRELLIS menggunakan **git submodule** untuk `flexicubes` (lihat `.gitmodules`). Perintah `git clone` tanpa `--recurse-submodules` membuat folder `flexicubes/` ada tetapi **kosong** (tidak ada file `.py`). Ini adalah akar masalah yang menyebabkan serangkaian `ModuleNotFoundError` sebelumnya — bukan karena paket pip yang kurang.
- **Solusi:** Mengganti `git clone https://github.com/Microsoft/TRELLIS.git` menjadi `git clone --recurse-submodules https://github.com/Microsoft/TRELLIS.git`.
- **Pelajaran:** Selalu periksa `.gitmodules` saat meng-clone repository ML/3D. Git submodules adalah pola umum di proyek riset yang mem-vendor dependensi internal.
- **Status:** ✅ Fixed

### [2026-07-08] [PHASE 4] — Kaolin Missing Module in Flexicubes
- **File & Baris:** `backend/services/modal_trellis.py` (Modal container runtime)
- **Pesan Error:** `ModuleNotFoundError: No module named 'kaolin'`
- **Penyebab:** Modul `flexicubes` (git submodule yang baru saja kita perbaiki) ternyata membutuhkan `kaolin` pada baris `from kaolin.utils.testing import check_tensor`.
- **Solusi:** Menambahkan instalasi `kaolin` secara eksplisit menggunakan wheel spesifik untuk CUDA 11.8 (`pip install kaolin -f https://nvidia-kaolin.s3.us-east-2.amazonaws.com/torch-2.4.0_cu118.html`) ke blok `run_commands`.
- **Status:** ✅ Fixed

### [2026-07-08] [PHASE 4] — nvdiffrast Installed as UNKNOWN Package / Build Error
- **File & Baris:** `backend/services/modal_trellis.py` (Modal container runtime)
- **Pesan Error:** `ModuleNotFoundError: No module named 'nvdiffrast'`
- **Penyebab:** 
  1. Instalasi awal `git+https` dengan pip gagal mendeteksi metadata paket, sehingga paket tersebut diinstal dengan nama `UNKNOWN-0.0.0`. 
  2. Saat dicoba clone manual, instalasi pip menolak berjalan karena secara eksplisit membutuhkan flag `--no-build-isolation` agar dapat menemukan environment PyTorch.
  3. Namun ketika `--no-build-isolation` digunakan, instalasi tetap gagal mem-parsing nama paket (`UNKNOWN-0.0.0` lagi, sehingga isi modul python-nya tidak terinstall). Ternyata `nvdiffrast` menggunakan standard PEP 621 (`pyproject.toml` dengan header `[project]`) yang HANYA didukung oleh `setuptools>=64` ke atas.
- **Solusi:** Memastikan instalasi `setuptools>=64` secara eksplisit sebelum menjalankan `pip install /tmp/nvdiffrast --no-build-isolation` agar pip dan setuptools dapat membaca `pyproject.toml` dengan baik.
- **Status:** ✅ Fixed

### [2026-07-08] [PHASE 4] — utils3d has no attribute 'torch'
- **File & Baris:** `backend/services/modal_trellis.py` (Modal container runtime) -> `trellis/utils/postprocessing_utils.py:57`
- **Pesan Error:** `AttributeError: module 'utils3d' has no attribute 'torch'`
- **Penyebab:** Modul `utils3d` standar dari PyPI tidak memiliki sub-modul `.torch` (kemungkinan karena pengembangan terpisah atau fitur tidak dirilis ke PyPI utama). TRELLIS secara diam-diam bergantung pada fork spesifik dari modul ini.
- **Solusi:** 
  1. Mengganti dependensi dari PyPI standar ke repo GitHub spesifik yang mengandung submodule `torch` (fork oleh `EasternJournalist`).
  2. Karena modul ini tidak dikemas dengan metadata PEP 621 standar yang dipahami oleh pip secara *default*, instalasinya terdeteksi sebagai `UNKNOWN-0.0.0` dan isi modulnya tidak dipindahkan.
  3. Mengubah instalasi dari *block* `.pip_install(...)` menjadi *block* `.run_commands(...)` menggunakan eksekusi eksplisit `git clone https://github.com/EasternJournalist/utils3d.git /tmp/utils3d && pip install /tmp/utils3d --no-build-isolation` agar instalasi langsung menggunakan struktur `setup.py` / `pyproject.toml` dengan mode developer (tanpa build environment isolasi) persis seperti yang kita lakukan pada `nvdiffrast`.
- **Status:** ✅ Fixed

---

*Error baru akan terus ditambahkan di sini setiap kali ditemukan selama pengembangan.*
