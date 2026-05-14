import asyncio
import httpx
from core.config import settings

MESHY_URL = "https://api.meshy.ai/v2/text-to-3d"
HEADERS = {
    "Authorization": f"Bearer {settings.MESHY_API_KEY}"
}

async def generate_3d_model_async(base_prompt: str, client: httpx.AsyncClient):
    enhanced_prompt = (
        f"A clean and professional 3D model of a {base_prompt}. "
        "Simple textures, mid-poly aesthetic, architectural model style, "
        "vibrant colors, well-lit, isometric view."
    )
    
    print(f"🪄 [FASE 1] Meminta Meshy membuat PREVIEW untuk: '{base_prompt}'...")

    preview_payload = {
        "mode": "preview", 
        "prompt": enhanced_prompt,
        "art_style": "realistic",
        "should_remesh": True
    }

    res_preview = await client.post(MESHY_URL, headers=HEADERS, json=preview_payload)
    if res_preview.status_code != 202:
        raise Exception(f"Meshy API Error (Preview) for {base_prompt}: {res_preview.text}")

    preview_task_id = res_preview.json().get("result")
    print(f"⏳ Task ID Preview {preview_task_id} dibuat! Menunggu mesh selesai...")

    elapsed_time = 0
    while True:
        await asyncio.sleep(10)
        elapsed_time += 10
        res = await client.get(f"{MESHY_URL}/{preview_task_id}", headers=HEADERS)
        data = res.json()
        status = data.get("status")
        
        if status == "SUCCEEDED":
            break
        elif status in ["FAILED", "EXPIRED", "CANCELED"]:
            raise Exception(f"Preview gagal untuk '{base_prompt}': {data.get('task_error')}")

    print(f"✨ Fase 1 '{base_prompt}' Selesai! Melanjutkan ke [FASE 2: REFINE]...")

    refine_payload = {
        "mode": "refine",
        "preview_task_id": preview_task_id
    }

    res_refine = await client.post(MESHY_URL, headers=HEADERS, json=refine_payload)
    if res_refine.status_code != 202:
        raise Exception(f"Meshy API Error (Refine) for {base_prompt}: {res_refine.text}")

    refine_task_id = res_refine.json().get("result")
    
    elapsed_time = 0
    while True:
        await asyncio.sleep(10)
        elapsed_time += 10
        res = await client.get(f"{MESHY_URL}/{refine_task_id}", headers=HEADERS)
        data = res.json()
        status = data.get("status")

        if status == "SUCCEEDED":
            model_urls = data.get("model_urls", {})
            glb_url = model_urls.get("glb")
            print(f"✅ Model 3D '{base_prompt}' selesai dirakit!")
            return {
                "task_id": refine_task_id,
                "model_url": glb_url,
                "status": status,
                "prompt": base_prompt
            }
        elif status in ["FAILED", "EXPIRED", "CANCELED"]:
            raise Exception(f"Refine gagal untuk '{base_prompt}': {data.get('task_error')}")

async def generate_multiple_models(prompts: list[str]):
    async with httpx.AsyncClient(timeout=120.0) as client:
        tasks = [generate_3d_model_async(prompt, client) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

def generate_3d_model(base_prompt: str):
    # Menyediakan fallback fungsi sinkronus agar tidak mematahkan kode lama yang memanggil secara sinkronus
    return asyncio.run(generate_multiple_models([base_prompt]))[0]

# --- SCRIPT PENGUJIAN SEMENTARA ---
if __name__ == "__main__":
    async def test_parallel():
        print("🚀 Memulai tes Meshy API Pipeline secara PARALEL...")
        test_prompts = ["sustainable bamboo pavilion", "small solar panel array"]
        start_time = time.time()
        
        hasil = await generate_multiple_models(test_prompts)
        
        print(f"\n⏱️ Waktu total: {time.time() - start_time:.2f} detik")
        print("\n🎉 HASIL URL GLB (TEXTURED):")
        for res in hasil:
            if isinstance(res, Exception):
                print(f"❌ Error: {res}")
            else:
                print(f"- {res['prompt']}: {res['model_url']}")

    import time
    asyncio.run(test_parallel())