import time
import requests
from core.config import settings

MESHY_URL = "https://api.meshy.ai/v2/text-to-3d"
HEADERS = {
    "Authorization": f"Bearer {settings.MESHY_API_KEY}"
}

def generate_3d_model(base_prompt: str):
    enhanced_prompt = (
        f"A clean and professional 3D model of a {base_prompt}. "
        "Simple textures, mid-poly aesthetic, architectural model style, "
        "vibrant colors, well-lit, isometric view."
    )
    
    print(f"🪄 [FASE 1] Meminta Meshy membuat PREVIEW (Bentuk Kasar) untuk:\n   '{base_prompt}'...")

    # ==========================================
    # FASE 1: PREVIEW TASK
    # ==========================================
    preview_payload = {
        "mode": "preview", 
        "prompt": enhanced_prompt,
        "art_style": "realistic",
        "should_remesh": True
    }

    res_preview = requests.post(MESHY_URL, headers=HEADERS, json=preview_payload)
    if res_preview.status_code != 202:
        raise Exception(f"Meshy API Error (Preview): {res_preview.text}")

    preview_task_id = res_preview.json().get("result")
    print(f"⏳ Task ID Preview {preview_task_id} dibuat! Menunggu mesh selesai...")

    # Polling Fase 1 (Dynamic While Loop)
    elapsed_time = 0
    while True:
        time.sleep(10)
        elapsed_time += 10
        res = requests.get(f"{MESHY_URL}/{preview_task_id}", headers=HEADERS).json()
        status = res.get("status")
        
        print(f"   [Preview] Status: {status}... ({elapsed_time} detik)")
        
        if status == "SUCCEEDED":
            break
        elif status in ["FAILED", "EXPIRED", "CANCELED"]:
            raise Exception(f"Preview gagal dirender: {res.get('task_error')}")

    print("✨ Fase 1 Selesai! Melanjutkan ke [FASE 2: REFINE] untuk baking tekstur PBR...")

    # ==========================================
    # FASE 2: REFINE TASK (Baking Texture)
    # ==========================================
    refine_payload = {
        "mode": "refine",
        "preview_task_id": preview_task_id
    }

    res_refine = requests.post(MESHY_URL, headers=HEADERS, json=refine_payload)
    if res_refine.status_code != 202:
        raise Exception(f"Meshy API Error (Refine): {res_refine.text}")

    refine_task_id = res_refine.json().get("result")
    print(f"⏳ Task ID Refine {refine_task_id} dibuat! Menunggu tekstur...")

    # Polling Fase 2 (Dynamic While Loop)
    elapsed_time = 0
    while True:
        time.sleep(10)
        elapsed_time += 10
        res = requests.get(f"{MESHY_URL}/{refine_task_id}", headers=HEADERS).json()
        status = res.get("status")
        
        # Print tiap 15 detik saja biar terminal tetap bersih
        if elapsed_time % 10 == 0 or status == "SUCCEEDED":
            print(f"   [Refine] Status: {status}... ({elapsed_time} detik)")

        if status == "SUCCEEDED":
            model_urls = res.get("model_urls", {})
            glb_url = model_urls.get("glb")
            print(f"✅ Model 3D bertekstur tinggi '{base_prompt}' selesai dirakit!")
            return {
                "task_id": refine_task_id,
                "model_url": glb_url,
                "status": status
            }
        elif status in ["FAILED", "EXPIRED", "CANCELED"]:
            raise Exception(f"Refine gagal dirender: {res.get('task_error')}")

# --- SCRIPT PENGUJIAN SEMENTARA ---
if __name__ == "__main__":
    try:
        print("🚀 Memulai tes Meshy API Pipeline (Preview + Refine)...")
        test_prompt = "sustainable bamboo educational pavilion"
        hasil = generate_3d_model(test_prompt)
        print("\n🎉 HASIL URL GLB (TEXTURED):", hasil["model_url"])
    except Exception as e:
        print("\n❌ ERROR:", e)