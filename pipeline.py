"""
pipeline.py — Orchestrator agent that chains:
  ContentExtractor → Summarizer → SlideGenerator

This is the single entry point for the full AI pipeline.
"""

import os
import time
from src.agents.content_extractor import ContentExtractor
from src.agents.summarizer import Summarizer
from src.agents.slide_generator import SlideGenerator


class PipelineAgent:
    """
    Agentic pipeline that orchestrates the full slide-generation workflow.

    Flow:
      1. Extract text from all files in a directory or a single file
      2. Summarize each document into structured slide data (JSON)
      3. Merge all documents into one cohesive presentation
      4. Generate and save the styled PowerPoint
    """

    def __init__(self, output_dir: str = "output/"):
        self.output_dir = output_dir
        self.extractor = ContentExtractor()
        self.summarizer = Summarizer()
        self.generator = SlideGenerator(output_dir=output_dir)

    def run_from_directory(self, directory: str, output_filename: str = "generated_presentation.pptx") -> str:
        """Run the full pipeline on all supported files in a directory."""
        print(f"\n{'='*60}")
        print(f"🤖 PipelineAgent starting...")
        print(f"   Source: {directory}")
        print(f"{'='*60}\n")

        # Step 1: Extract
        print("📄 Step 1: Extracting content from files...")
        self.extractor.directory = directory
        extracted = self.extractor.extract_from_directory()

        if not extracted:
            raise ValueError(f"No supported files found in: {directory}")

        # Step 2: Summarize all files, merge slides
        print(f"\n🧠 Step 2: Summarizing {len(extracted)} file(s) with AI...")
        all_slides = []
        presentation_title = "AI-Generated Presentation"
        subtitle = "Automatically generated from your documents"
        theme_color = "blue"

        for i, (filename, text) in enumerate(extracted.items()):
            print(f"\n  [{i+1}/{len(extracted)}] Processing: {filename}")
            try:
                structured = self.summarizer.summarize_text(text)

                # Use title/theme from first document
                if i == 0:
                    presentation_title = structured.get("presentation_title", presentation_title)
                    subtitle = structured.get("subtitle", subtitle)
                    theme_color = structured.get("theme_color", theme_color)

                slides = structured.get("slides", [])
                # Tag slides with source file if multiple files
                if len(extracted) > 1:
                    for slide in slides:
                        slide["slide_title"] = f"{slide.get('slide_title', '')} [{filename}]"

                all_slides.extend(slides)
                print(f"  ✓ Got {len(slides)} slides from {filename}")

                # Small delay to avoid rate limiting
                if i < len(extracted) - 1:
                    time.sleep(1)

            except Exception as e:
                print(f"  ✗ Failed to summarize {filename}: {e}")
                continue

        if not all_slides:
            raise RuntimeError("Summarization produced no slides. Check your GROQ_API_KEY.")

        # Step 3: Generate
        print(f"\n🎨 Step 3: Generating styled PowerPoint ({len(all_slides)} slides)...")
        merged_data = {
            "presentation_title": presentation_title,
            "subtitle": subtitle,
            "theme_color": theme_color,
            "slides": all_slides,
        }

        pptx_path = self.generator.create_slide_deck(merged_data, output_filename)

        print(f"\n{'='*60}")
        print(f"✅ Pipeline complete!")
        print(f"   Output: {pptx_path}")
        print(f"   Slides: {len(all_slides) + 1} (including cover)")
        print(f"{'='*60}\n")

        return pptx_path

    def run_from_file(self, file_path: str, output_filename: str = "generated_presentation.pptx") -> str:
        """Run the full pipeline on a single file."""
        print(f"\n🤖 PipelineAgent processing: {file_path}")

        # Step 1: Extract
        print("📄 Extracting content...")
        text = self.extractor.extract_from_file(file_path)

        if not text.strip():
            raise ValueError(f"No text content found in: {file_path}")

        # Step 2: Summarize
        print("🧠 Summarizing with AI...")
        structured = self.summarizer.summarize_text(text)

        # Step 3: Generate
        slides = structured.get("slides", [])
        print(f"🎨 Generating PowerPoint ({len(slides)} slides)...")
        pptx_path = self.generator.create_slide_deck(structured, output_filename)

        print(f"✅ Done! Saved to: {pptx_path}\n")
        return pptx_path


if __name__ == "__main__":
    agent = PipelineAgent(output_dir="output/")
    agent.run_from_directory("data/")