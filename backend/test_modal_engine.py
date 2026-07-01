import asyncio
import os
import sys

# Ensure backend dir is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.modal_engine import modal_engine

async def main():
    components = [
        {"name": "Solar Panel", "sd_xl_prompt": "A modern solar panel on clean white background, isometric view"},
        {"name": "Wind Turbine", "sd_xl_prompt": "A miniature wind turbine on clean white background, isometric view"},
    ]
    
    print("🚀 Testing ModalEngine.generate_multiple_3d with 2 parallel prompts...")
    results = await modal_engine.generate_multiple_3d(components)
    
    for res in results:
        name = res["name"]
        if res["error"]:
            print(f"❌ Failed for {name}: {res['error']}")
        else:
            glb_bytes = res["glb_bytes"]
            filename = f"test_{name.replace(' ', '_').lower()}.glb"
            with open(filename, "wb") as f:
                f.write(glb_bytes)
            print(f"✅ Success for {name}! Saved to {filename} ({len(glb_bytes)/1024:.1f} KB)")

if __name__ == "__main__":
    asyncio.run(main())
