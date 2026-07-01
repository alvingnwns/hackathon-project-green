"""
Modal.com serverless deployment for SD-XL 1.0 base model.
Generates images from text prompts (image-to-image pipeline without input image).

Architecture:
  - Deploys on Modal's Nvidia A10G 24GB
  - Text-to-Image generation with Stable Diffusion XL 1.0 base
  - Output: clean image with plain/transparent background for SF3D
"""

import io
import modal
from modal import App, Image

# --- Modal App Definition ---
app = modal.App("greenscape-sd-xl")

# --- Build a Modal Image with all dependencies ---
sd_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.0-devel-ubuntu22.04",
        setup_dockerfile_commands=[
            "RUN apt-get update && apt-get install -y python3 python3-pip git python-is-python3",
        ]
    )
    .pip_install(
        "torch==2.6.0",
        "diffusers==0.32.1",
        "transformers==4.48.0",
        "accelerate==1.3.0",
        "safetensors==0.5.1",
        "pillow==11.1.0",
        "huggingface_hub==0.29.0",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

# Model path constant
MODEL_NAME = "stabilityai/stable-diffusion-xl-base-1.0"

@app.cls(
    image=sd_image,
    gpu="A10G",
    timeout=300,
)
class SDXLGenerator:
    # Model diinisialisasi secara dinamis di load_model (modal.enter),
    # menghindari constructor __init__ yang tidak didukung Modal.

    @modal.enter()
    def load_model(self):
        """Load SD-XL model into GPU memory (called once per container)."""
        import torch  # type: ignore
        from diffusers import StableDiffusionXLPipeline  # type: ignore

        print("🚀 Loading SD-XL 1.0 base model onto GPU...")
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float16,
            use_safetensors=True,
            variant="fp16",
        )
        self.pipe = self.pipe.to("cuda")
        self.pipe.enable_model_cpu_offload()
        self.pipe.enable_attention_slicing()
        print("✅ SD-XL model loaded and ready!")

    @modal.method()
    def generate(self, prompt: str, negative_prompt: str = "") -> bytes:
        """
        Generate an image from a text prompt.

        Args:
            prompt: The text prompt for image generation (from Gemini's sd_xl_prompt).
            negative_prompt: Things to avoid in the generated image.

        Returns:
            PNG image as bytes with clean background suitable for SF3D.
        """
        import torch  # type: ignore
        from PIL import Image as PILImage  # type: ignore

        if negative_prompt == "":
            negative_prompt = (
                "people, animals, text, watermark, signature, "
                "complex background, cluttered scene, low quality, blurry"
            )

        print(f"🎨 Generating image for prompt: '{prompt[:80]}...'")

        with torch.inference_mode():
            result = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=30,
                guidance_scale=7.5,
                width=1024,
                height=1024,
            )

        image = result.images[0]

        # Save to bytes
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        print(f"✅ Image generated: {buf.getbuffer().nbytes / 1024:.1f} KB")
        return buf.getvalue()


    @modal.method()
    def warm(self) -> str:
        """Lightweight method to keep the container alive without generating."""
        return "SD-XL container is warm"

# --- Standalone test ---
@app.local_entrypoint()
def main():
    generator = SDXLGenerator()
    test_prompt = "A single modern solar panel on clean white background, isometric view, professional product photography"
    print("🧪 Testing SD-XL generation...")
    img_bytes = generator.generate.remote(test_prompt)
    output_path = "test_sdxl_output.png"
    with open(output_path, "wb") as f:
        f.write(img_bytes)
    print(f"✅ Test image saved to {output_path} ({len(img_bytes) / 1024:.1f} KB)")