"""
Modal.com Engine — Orchestrator for parallel SD-XL + SF3D pipeline.

This module manages the parallel execution of:
  1. SD-XL text-to-image generation (multiple prompts concurrently)
  2. SF3D image-to-3D reconstruction (multiple images concurrently)

All calls are dispatched to Modal.com serverless functions.
"""

import asyncio
import io
from typing import List, Optional

from core.config import settings

# Import Modal app classes
from services.modal_sd_xl import SDXLGenerator


class ModalPipelineError(Exception):
    """Custom exception for Modal pipeline failures."""
    pass


import modal

class ModalEngine:
    """
    Orchestrates the parallel pipeline: SD-XL → SF3D for multiple components.
    
    Usage:
        engine = ModalEngine()
        results = await engine.generate_component_3d_models([
            {"sd_xl_prompt": "A greenhouse...", "name": "Greenhouse"},
            {"sd_xl_prompt": "A solar panel...", "name": "Solar Panel"},
        ])
    """

    def __init__(self):
        self._sd_generator = None

    def _ensure_initialized(self):
        if self._sd_generator is None:
            print("🔍 Looking up deployed Modal endpoints...")
            sd_cls = modal.Cls.from_name("greenscape-sd-xl", "SDXLGenerator")
            self._sd_generator = sd_cls()

    async def _run_sd_xl(self, prompt: str) -> bytes:
        """
        Calls the SD-XL modal function using native Modal async (.aio)
        """
        self._ensure_initialized()
        # .remote.aio is Modal's native async caller
        result = await self._sd_generator.generate.remote.aio(prompt)
    async def generate_single_image(self, prompt: str) -> bytes:
        """
        SD-XL text-to-image pipeline for a single component.

        Args:
            prompt: The sd_xl_prompt from Gemini analysis.

        Returns:
            PNG file bytes.

        Raises:
            ModalPipelineError: If SD-XL fails.
        """
        try:
            print(f"🎨 [Modal] SD-XL generating image for prompt...")
            img_bytes = await self._run_sd_xl(prompt)
            print(f"✅ [Modal] Image generated ({len(img_bytes) / 1024:.1f} KB).")
            return img_bytes
        except Exception as e:
            raise ModalPipelineError(f"Modal pipeline failed for prompt '{prompt[:60]}': {e}")

    async def generate_multiple_images(
        self, components: List[dict]
    ) -> List[dict]:
        """
        Run parallel SD-XL pipelines for multiple components.

        Args:
            components: List of dicts, each with at least:
                - "sd_xl_prompt": str — The prompt for SD-XL
                - "name": str — Component name for error reporting

        Returns:
            List of dicts, each with:
                - "name": str — Component name
                - "img_bytes": bytes | None — PNG bytes from SD-XL
                - "error": str | None — Error message if failed
        """
        if not components:
            return []

        tasks = []
        for comp in components:
            prompt = comp.get("sd_xl_prompt", "")
            name = comp.get("name", "unknown")
            if not prompt:
                print(f"⚠️ [Modal] No sd_xl_prompt for '{name}', skipping.")
                tasks.append(self._failed_result(name, "No sd_xl_prompt provided"))
            else:
                tasks.append(self._generate_single_wrapped(name, prompt))

        print(f"🚀 [Modal] Launching {len(tasks)} parallel SD-XL pipelines...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    "name": components[i].get("name", f"component_{i}"),
                    "img_bytes": None,
                    "error": str(result),
                })
            else:
                final_results.append(result)

        return final_results

    async def _generate_single_wrapped(self, name: str, prompt: str) -> dict:
        """Wrap single generation with error handling."""
        try:
            img_bytes = await self.generate_single_image(prompt)
            return {"name": name, "img_bytes": img_bytes, "error": None}
        except Exception as e:
            return {"name": name, "img_bytes": None, "error": str(e)}

    def _failed_result(self, name: str, error: str) -> dict:
        """Create a placeholder failed result."""
        future = asyncio.Future()
        future.set_result({"name": name, "img_bytes": None, "error": error})
        return future


# Singleton instance
modal_engine = ModalEngine()