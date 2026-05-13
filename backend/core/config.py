import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "Permaculture 3D Engine"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/heic", "image/heif"]

    def __init__(self):
        if not self.GOOGLE_API_KEY:
            raise ValueError("🚨API key tidak ditemukan di .env!")

settings = Settings()