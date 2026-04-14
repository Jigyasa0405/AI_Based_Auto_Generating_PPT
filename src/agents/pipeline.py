"""
pipeline.py — Orchestrator agent that chains:
  ContentExtractor → Summarizer → ImageGenerator → SlideGenerator
"""

import os
import time
from src.agents.content_extractor import ContentExtractor
from src.agents.summarizer import Summarizer
from src.agents.image_generator import ImageGenerator
from src.agents.slide_generator import SlideGenerator


class PipelineAgent:
    """
    Agentic pipeline orchestrating the full slide-generation workflow.

    Flow:
      1. Extract text from all files in a directory (or single file)
      2. Summarize each document → structured JSON (title, slides, theme)
      3. Fetch/generate one image per content slide (free, cached)
      4. Build and save a styled PowerPoint with images embedded
    """

    def __init__(self, output_dir: str = "output/", enable_images: bool = True):
        self.output_dir    = output_dir
        self.enable_images = enable_images
        self.extractor     = ContentExtractor()
        self.summarizer    = Summarizer()
        self.img_gen       = ImageGenerator()
        self.generator     = SlideGenerator(output_dir=output_dir)

    def run_from_directory(self, directory: str,
                           output_filename: str = "generated_presentation.pptx") -> str:
        """Run the full pipeline on all supported files in a directory."""
        print(f"\n{'='*60}")
        print(f"🤖 PipelineAgent starting...")
        print(f"   Source : {directory}")
        print(f"   Images : {'enabled' if self.enable_images else 'disabled'}")
        print(f"{'='*60}\n")

        # ── Step 1: Extract ───────────────────────────────────────────────────
        print("📄 Step 1: Extracting content from files...")
        self.extractor.directory = directory
        extracted = self.extractor.extract_from_directory()

        if not extracted:
            raise ValueError(f"No supported files found in: {directory}")

        # ── Step 2: Summarise all files → merge slides ─────────────────────
        print(f"\n🧠 Step 2: Summarising {len(extracted)} file(s) with AI...")
        all_slides: list       = []
        presentation_title     = "AI-Generated Presentation"
        subtitle               = "Automatically generated from your documents"
        theme_color            = "blue"

        for i, (filename, text) in enumerate(extracted.items()):
            print(f"\n  [{i+1}/{len(extracted)}] Processing: {filename}")
            try:
                structured = self.summarizer.summarize_text(text)

                if i == 0:
                    presentation_title = structured.get("presentation_title", presentation_title)
                    subtitle           = structured.get("subtitle", subtitle)
                    theme_color        = structured.get("theme_color", theme_color)

                slides = structured.get("slides", [])
                if len(extracted) > 1:
                    for slide in slides:
                        slide["slide_title"] = f"{slide.get('slide_title', '')}  [{filename}]"

                all_slides.extend(slides)
                print(f"  ✓ {len(slides)} slides from {filename}")

                if i < len(extracted) - 1:
                    time.sleep(1)   # Groq rate-limit courtesy pause

            except Exception as e:
                print(f"  ✗ Failed to summarise {filename}: {e}")

        if not all_slides:
            raise RuntimeError("Summarisation produced no slides. Check GROQ_API_KEY.")

        # ── Step 3: Fetch images ───────────────────────────────────────────
        image_map: dict = {}
        if self.enable_images:
            print(f"\n🖼  Step 3: Fetching images for content slides...")
            try:
                image_map = self.img_gen.get_images_for_presentation(all_slides)
                print(f"  ✓ Images ready for {len(image_map)} slide(s)")
            except Exception as e:
                print(f"  ⚠  Image generation skipped: {e}")
        else:
            print("\n🖼  Step 3: Image generation disabled — skipping.")

        # ── Step 4: Build PowerPoint ──────────────────────────────────────
        print(f"\n🎨 Step 4: Building PowerPoint ({len(all_slides)} content slides)...")
        merged_data = {
            "presentation_title": presentation_title,
            "subtitle":           subtitle,
            "theme_color":        theme_color,
            "slides":             all_slides,
        }
        pptx_path = self.generator.create_slide_deck(
            merged_data, output_filename, image_map=image_map
        )

        print(f"\n{'='*60}")
        print(f"✅ Pipeline complete!")
        print(f"   Output : {pptx_path}")
        print(f"   Slides : {len(all_slides) + 1} total (incl. cover)")
        print(f"   Images : {len(image_map)} embedded")
        print(f"{'='*60}\n")

        return pptx_path

    def run_from_file(self, file_path: str,
                      output_filename: str = "generated_presentation.pptx") -> str:
        """Run the full pipeline on a single file."""
        print(f"\n🤖 PipelineAgent processing: {file_path}")

        print("📄 Extracting content...")
        text = self.extractor.extract_from_file(file_path)
        if not text.strip():
            raise ValueError(f"No text content found in: {file_path}")

        print("🧠 Summarising with AI...")
        structured = self.summarizer.summarize_text(text)
        slides     = structured.get("slides", [])

        image_map: dict = {}
        if self.enable_images:
            print("🖼  Fetching images...")
            try:
                image_map = self.img_gen.get_images_for_presentation(slides)
            except Exception as e:
                print(f"  ⚠  Image fetch skipped: {e}")

        print(f"🎨 Building PowerPoint ({len(slides)} slides)...")
        pptx_path = self.generator.create_slide_deck(
            structured, output_filename, image_map=image_map
        )

        print(f"✅ Done! Saved to: {pptx_path}\n")
        return pptx_path


if __name__ == "__main__":
    agent = PipelineAgent(output_dir="output/", enable_images=True)
    agent.run_from_directory("data/")