import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "Permaculture 3D Engine"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    HF_API_TOKEN = os.getenv("HF_API_TOKEN")
    MESHY_API_KEY = os.getenv("MESHY_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/heic", "image/heif"]

    def __init__(self):
        if not self.GEMINI_API_KEY:
            raise ValueError("🚨GEMINI_API_KEY tidak ditemukan di .env!")
        if not self.HF_API_TOKEN:
            raise ValueError("🚨HF_API_TOKEN tidak ditemukan di .env!")
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            print("⚠️ SUPABASE_URL atau SUPABASE_KEY belum diset. Fitur Storage tidak akan berjalan optimal.")

settings = Settings()