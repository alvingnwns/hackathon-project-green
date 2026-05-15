import httpx
from supabase import create_client, Client
from core.config import settings
import uuid

# Inisialisasi Supabase Client
supabase: Client = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def upload_meshy_to_supabase(asset_name: str, meshy_url: str) -> str:
    """
    Mengunduh .glb dari url Meshy, menyimpannya sementara di memori,
    lalu mengunggahnya ke Supabase Object Storage (Bucket 'green_assets').
    Mengembalikan URL public dari Supabase.
    """
    if not supabase:
        print("⚠️ Supabase belum di-setup, mengembalikan url asli dari Meshy saja.")
        return meshy_url

    try:
        print(f"📥 Mengunduh model dari Meshy: {asset_name}...")
        async with httpx.AsyncClient() as client:
            resp = await client.get(meshy_url, timeout=60.0)
            if resp.status_code != 200:
                print(f"❌ Gagal mengunduh file dari Meshy (Status {resp.status_code})")
                return meshy_url
            file_bytes = resp.content
        
        # Buat nama unik untuk menghindari konflik nama yang sama
        clean_name = asset_name.replace(":", "").replace(" ", "_").lower()[:30]
        unique_filename = f"{clean_name}_{uuid.uuid4().hex[:8]}.glb"
        
        print(f"☁️ Mengunggah {unique_filename} ke Supabase Storage (bucket: glb_models)...")
        # Upload ke bucket "glb_models"
        res = supabase.storage.from_("glb_models").upload(
            file=file_bytes,
            path=unique_filename,
            file_options={"content-type": "model/gltf-binary"}
        )
        
        # Dapatkan URL publiknya
        public_url = supabase.storage.from_("glb_models").get_public_url(unique_filename)
        print(f"✅ Supabase URL didapatkan: {public_url}")
        
        return public_url

    except Exception as e:
        print(f"❌ Terjadi kesalahan saat upload ke Supabase: {e}")
        return meshy_url
