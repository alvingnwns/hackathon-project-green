"""
Supabase Engine — CRUD operations for Supabase Storage + Database.

Supports both legacy Meshy flow and new Modal flow:
  - Upload raw images (from user) to 'raw_images' bucket
  - Upload .glb bytes (from SF3D) to 'glb_models' bucket
  - Save project metadata to PostgreSQL 'projects' table
  - Get public URLs for stored assets
"""

import io
import uuid
from typing import Optional
import httpx
from supabase import create_client, Client
from core.config import settings

# Inisialisasi Supabase Client
supabase: Client = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def _get_unique_filename(name: str, extension: str = ".glb") -> str:
    """Generate a unique filename with a short UUID to avoid collisions."""
    clean_name = name.replace(":", "").replace(" ", "_").lower()[:30]
    return f"{clean_name}_{uuid.uuid4().hex[:8]}{extension}"


def _ensure_bucket(bucket_name: str) -> bool:
    """
    Cek apakah bucket ada di Supabase Storage. Jika belum, buat otomatis.
    Returns True jika bucket ready/siap, False jika gagal.
    """
    if not supabase:
        return False
    try:
        # Coba list buckets
        buckets = supabase.storage.list_buckets()
        existing = [b.name for b in buckets]

        if bucket_name not in existing:
            print(f"🪣 Bucket '{bucket_name}' belum ada. Membuat otomatis...")
            supabase.storage.create_bucket(
                id=bucket_name,
                name=bucket_name,
                options={"public": True}
            )
            print(f"✅ Bucket '{bucket_name}' berhasil dibuat!")
        else:
            print(f"✅ Bucket '{bucket_name}' sudah tersedia.")

        # Pastikan bucket public
        supabase.storage.update_bucket(
            id=bucket_name,
            options={"public": True}
        )
        return True
    except Exception as e:
        print(f"⚠️ Gagal mengecek/membuat bucket '{bucket_name}': {e}")
        print(f"   Buat bucket '{bucket_name}' manual di Supabase Dashboard > Storage > New Bucket (public)")
        return False


async def upload_raw_image(image_bytes: bytes, original_filename: str = "upload") -> Optional[str]:
    """
    Upload a raw image (from user upload) to Supabase Storage bucket 'raw_images'.

    Args:
        image_bytes: The raw image file bytes.
        original_filename: Original filename for naming convention.

    Returns:
        Public URL of the uploaded image, or None on failure.
    """
    if not supabase:
        print("⚠️ Supabase belum di-setup, tidak dapat upload raw image.")
        return None

    bucket_name = settings.SUPABASE_BUCKET_RAW  # "raw_images"
    try:
        # Determine file extension from original filename
        ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "jpg"
        unique_filename = _get_unique_filename(original_filename.replace(f".{ext}", ""), f".{ext}")

        print(f"☁️ Mengunggah raw image ke Supabase Storage (bucket: {bucket_name})...")
        
        def _upload():
            if not _ensure_bucket(bucket_name):
                print(f"⚠️ Bucket '{bucket_name}' tidak tersedia, skip upload raw image.")
                return False
                
            supabase.storage.from_(bucket_name).upload(
                file=image_bytes,
                path=unique_filename,
                file_options={"content-type": f"image/{ext}" if ext != "heic" else "image/heic"}
            )
        
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, _upload)

        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
        print(f"✅ Raw image URL: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ Gagal upload raw image ke Supabase: {e}")
        return None

async def upload_generated_image(asset_name: str, image_bytes: bytes) -> Optional[str]:
    """
    Upload a generated 2D image (from SD-XL) to Supabase Storage bucket 'raw_images'.

    Args:
        asset_name: Name of the asset (for filename).
        image_bytes: The generated PNG image as bytes.

    Returns:
        Public URL of the uploaded image, or None on failure.
    """
    if not supabase:
        return None

    bucket_name = settings.SUPABASE_BUCKET_RAW
    try:
        unique_filename = _get_unique_filename(asset_name, ".png")

        print(f"☁️ Mengunggah SDXL image ke Supabase Storage (bucket: {bucket_name})...")
        
        def _upload_img():
            if not _ensure_bucket(bucket_name):
                return False
                
            supabase.storage.from_(bucket_name).upload(
                file=image_bytes,
                path=unique_filename,
                file_options={"content-type": "image/png"}
            )
            
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, _upload_img)

        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
        print(f"✅ SDXL Image URL: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ Gagal upload SDXL image ke Supabase: {e}")
        return None


async def upload_glb_bytes(asset_name: str, glb_bytes: bytes) -> Optional[str]:
    """
    Upload .glb bytes (from SF3D) to Supabase Storage bucket 'glb_models'.

    Args:
        asset_name: Name of the asset (for filename).
        glb_bytes: The .glb file as bytes.

    Returns:
        Public URL of the uploaded .glb, or None on failure.
    """
    if not supabase:
        print("⚠️ Supabase belum di-setup, tidak dapat upload GLB.")
        return None

    bucket_name = settings.SUPABASE_BUCKET_GLB  # "glb_models"
    try:
        unique_filename = _get_unique_filename(asset_name, ".glb")

        print(f"☁️ Mengunggah GLB ke Supabase Storage (bucket: {bucket_name})...")
        
        def _upload_glb():
            if not _ensure_bucket(bucket_name):
                print(f"⚠️ Bucket '{bucket_name}' tidak tersedia, skip upload GLB.")
                return False
                
            supabase.storage.from_(bucket_name).upload(
                file=glb_bytes,
                path=unique_filename,
                file_options={"content-type": "model/gltf-binary"}
            )
            
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, _upload_glb)

        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
        print(f"✅ GLB URL: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ Gagal upload GLB ke Supabase: {e}")
        return None


async def upload_meshy_to_supabase(asset_name: str, meshy_url: str) -> str:
    """
    [LEGACY] Mengunduh .glb dari url Meshy, lalu mengunggahnya ke Supabase.
    Dipertahankan untuk backward compatibility.
    """
    if not supabase:
        print("⚠️ Supabase belum di-setup, mengembalikan url asli dari Meshy saja.")
        return meshy_url

    try:
        print(f"📥 [Legacy] Mengunduh model dari Meshy: {asset_name}...")
        async with httpx.AsyncClient() as client:
            resp = await client.get(meshy_url, timeout=60.0)
            if resp.status_code != 200:
                print(f"❌ Gagal mengunduh file dari Meshy (Status {resp.status_code})")
                return meshy_url
            file_bytes = resp.content

        # Reuse the GLB upload function
        result_url = await upload_glb_bytes(asset_name, file_bytes)
        return result_url or meshy_url

    except Exception as e:
        print(f"❌ Terjadi kesalahan saat upload ke Supabase: {e}")
        return meshy_url


def save_project_to_db(payload: dict, raw_image_url: Optional[str] = None) -> dict:
    """
    Menyimpan metadata project dan raw JSON ke tabel 'projects' di Supabase Database.

    Args:
        payload: Full pipeline result payload dict.
        raw_image_url: Public URL of the raw uploaded image (from Supabase Storage).
                       Disematkan ke dalam raw_json agar ter-link ke storage asset.
    """
    if not supabase:
        print("⚠️ Supabase belum di-setup, melewati proses simpan ke database.")
        return None

    try:
        full_report = payload.get("project_context", {}).get("gemini_full_report", {})
        concept = payload.get("project_context", {}).get("concept", "Untitled Project")
        cost = full_report.get("green_solution", {}).get("estimated_cost", 0)

        # Embed raw_image_url ke dalam payload sebelum disimpan ke DB
        # Ini menghindari ALTER TABLE dan tetap menjaga linking Storage ↔ DB
        if raw_image_url:
            payload["raw_image_url"] = raw_image_url

        db_payload = {
            "concept_name": concept,
            "estimated_cost": cost,
            "raw_json": payload
        }

        print("💾 Menyimpan metadata dan JSON ke Supabase Database...")
        response = supabase.table("projects").insert(db_payload).execute()
        return response.data
    except Exception as e:
        print(f"❌ Gagal menyimpan JSON ke database Supabase: {e}")
        return None


def get_project_by_id(project_id: str) -> Optional[dict]:
    """
    Fetch a project by its UUID from the 'projects' table.
    """
    if not supabase:
        return None
    try:
        response = supabase.table("projects").select("*").eq("id", project_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"❌ Gagal mengambil project {project_id}: {e}")
        return None


def list_recent_projects(limit: int = 20) -> list:
    """
    List recent projects ordered by creation date.
    """
    if not supabase:
        return []
    try:
        response = supabase.table("projects").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data or []
    except Exception as e:
        print(f"❌ Gagal mengambil daftar project: {e}")
        return []