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

---

*Error baru akan terus ditambahkan di sini setiap kali ditemukan selama pengembangan.*
