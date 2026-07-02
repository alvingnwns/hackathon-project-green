import asyncio
import httpx
import os
import sys
import time

async def test_e2e():
    print("🚀 Starting End-to-End Test (dry_run=true)...")
    url = "http://127.0.0.1:8000/api/v1/process-landscape?dry_run=true"
    test_image_path = "c:/Users/leona/OneDrive/Documents/ORCA/hackathon-project-green/backend/test_data/sample.jpg"
    
    # Create a dummy image if it doesn't exist
    os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
    if not os.path.exists(test_image_path):
        from PIL import Image
        img = Image.new('RGB', (1024, 1024), color = 'white')
        img.save(test_image_path)
    
    # 1. Upload image and start task
    async with httpx.AsyncClient() as client:
        with open(test_image_path, "rb") as f:
            files = {"file": ("sample.jpg", f, "image/jpeg")}
            try:
                response = await client.post(url, files=files, timeout=60.0)
            except Exception as e:
                print(f"❌ Failed to connect: {e}")
                return
                
        if response.status_code != 202:
            print(f"❌ Error starting task: {response.status_code} {response.text}")
            return
            
        data = response.json()
        task_id = data.get("task_id")
        print(f"✅ Task started successfully. Task ID: {task_id}")
        
        # 2. Poll the status
        status_url = f"http://127.0.0.1:8000/api/v1/tasks/{task_id}"
        is_done = False
        while not is_done:
            await asyncio.sleep(3)
            status_res = await client.get(status_url, timeout=60.0)
            task_data = status_res.json()
            
            print(f"⏳ Status: {task_data['status']} | Progress: {task_data['progress']}")
            
            if task_data["status"] == "completed":
                print("🎉 Pipeline completed successfully!")
                result = task_data["result"]
                print(f"Result has {len(result['assets'])} assets.")
                for a in result['assets']:
                    print(f" - {a['name']}: {a['model_url']}")
                is_done = True
            elif task_data["status"] == "failed":
                print(f"❌ Pipeline failed: {task_data.get('error')}")
                is_done = True

if __name__ == "__main__":
    asyncio.run(test_e2e())
