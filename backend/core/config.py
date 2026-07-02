import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "GreenScape AI — 2D-to-3D Generative Pipeline"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    HF_API_TOKEN = os.getenv("HF_API_TOKEN")
    MESHY_API_KEY = os.getenv("MESHY_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    MODAL_TOKEN_ID = os.getenv("MODAL_TOKEN_ID")
    MODAL_TOKEN_SECRET = os.getenv("MODAL_TOKEN_SECRET")
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/heic", "image/heif"]
    SUPABASE_BUCKET_GLB = "glb_models"
    SUPABASE_BUCKET_RAW = "raw_images"
    MODAL_KEEP_WARM_MINUTES = 10

    def __init__(self):
        if not self.GEMINI_API_KEY:
            raise ValueError("🚨 GEMINI_API_KEY tidak ditemukan di .env!")
        if not self.HF_API_TOKEN:
            raise ValueError("🚨 HF_API_TOKEN tidak ditemukan di .env!")
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            print("⚠️ SUPABASE_URL atau SUPABASE_KEY belum diset. Fitur Storage tidak akan berjalan optimal.")
        if not self.MODAL_TOKEN_ID or not self.MODAL_TOKEN_SECRET:
            print("⚠️ MODAL_TOKEN_ID atau MODAL_TOKEN_SECRET belum diset. Pipeline 3D via Modal tidak akan berfungsi.")

settings = Settings()