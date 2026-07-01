import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from core.config import settings
from api.router import router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Modular Backend Architecture"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan semua endpoint dari router
app.include_router(router, prefix="/api/v1")

# Mount folder static untuk menyimpan model 3D lokal jika Supabase gagal
os.makedirs("static/models", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)