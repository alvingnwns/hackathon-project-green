import asyncio
import os
import sys

# Ensure backend dir is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.supabase_engine import upload_glb_bytes

async def main():
    file_path = "test_solar_panel.glb"
    
    if not os.path.exists(file_path):
        print(f"❌ File {file_path} not found.")
        return
        
    print(f"🚀 Testing Supabase upload with {file_path}...")
    
    with open(file_path, "rb") as f:
        glb_bytes = f.read()
        
    url = await upload_glb_bytes("Solar Panel Test", glb_bytes)
    
    if url:
        print(f"✅ Upload success! URL: {url}")
    else:
        print(f"❌ Upload failed.")

if __name__ == "__main__":
    asyncio.run(main())
