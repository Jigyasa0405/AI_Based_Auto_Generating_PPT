"""
image_generator.py — Fetches or generates relevant images for slides.

Strategy (both FREE, no paid keys):
  1. Unsplash (free API) — photographic images by keyword
  2. Pollinations.AI  — AI image generation, no key required

Usage:
    gen = ImageGenerator()
    path = gen.get_image_for_slide("machine learning neural network", slide_index=0)
    # Returns a local file path to a .jpg/.png, or None on failure
"""

import os
import re
import time
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")   # optional — free at unsplash.com/developers
IMAGE_CACHE_DIR = "output/slide_images"


class ImageGenerator:
    """
    Fetches relevant images for slide topics using free services.
    Images are cached locally so repeated runs are fast.
    """

    POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1024&height=576&nologo=true&seed={seed}"
    UNSPLASH_URL     = "https://api.unsplash.com/photos/random"

    # Topics that work better with AI generation than stock photos
    AI_GEN_KEYWORDS = {
        "artificial intelligence", "machine learning", "neural network",
        "deep learning", "algorithm", "data science", "blockchain",
        "quantum", "future", "abstract", "concept", "technology",
        "innovation", "digital transformation",
    }

    def __init__(self, cache_dir: str = IMAGE_CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "AI-PPT-Generator/2.0"})

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_image_for_slide(self, topic: str, slide_index: int = 0) -> str | None:
        """
        Returns a local file path for an image relevant to `topic`.
        Returns None if all sources fail.
        """
        topic = topic.strip()
        if not topic:
            return None

        cache_path = self._cache_path(topic, slide_index)
        if os.path.exists(cache_path):
            print(f"    🖼  Cache hit: {os.path.basename(cache_path)}")
            return cache_path

        print(f"    🖼  Fetching image for: '{topic}'")

        # Choose source based on topic
        if self._is_abstract_topic(topic) or not UNSPLASH_ACCESS_KEY:
            image_data = self._from_pollinations(topic, slide_index)
        else:
            image_data = self._from_unsplash(topic)
            if image_data is None:
                image_data = self._from_pollinations(topic, slide_index)

        if image_data:
            with open(cache_path, "wb") as f:
                f.write(image_data)
            print(f"    ✓  Saved: {os.path.basename(cache_path)}")
            return cache_path

        print(f"    ✗  Could not fetch image for: '{topic}'")
        return None

    def get_images_for_presentation(self, slides: list[dict], max_images: int = 6) -> dict[int, str]:
        """
        Given a list of slide dicts (with 'slide_title' and 'bullet_points'),
        returns a mapping of {slide_index: image_path} for slides that get images.

        Skips intro (index 0) and conclusion (last) slides by default.
        """
        image_map: dict[int, str] = {}
        count = 0

        for i, slide in enumerate(slides):
            if count >= max_images:
                break

            slide_type = slide.get("slide_type", "content")
            if slide_type in ("intro", "conclusion"):
                continue

            # Build a rich search query from title + first bullet
            title = slide.get("slide_title", "")
            bullets = slide.get("bullet_points", [])
            query = self._build_query(title, bullets)

            path = self.get_image_for_slide(query, slide_index=i)
            if path:
                image_map[i] = path
                count += 1

            time.sleep(0.4)   # be polite to free APIs

        return image_map

    def clear_cache(self):
        """Remove all cached images."""
        for f in Path(self.cache_dir).glob("*"):
            f.unlink()
        print(f"  🗑  Image cache cleared: {self.cache_dir}")

    # ── Private helpers ────────────────────────────────────────────────────────

    def _cache_path(self, topic: str, slide_index: int) -> str:
        key = f"{topic}_{slide_index}"
        hash_str = hashlib.md5(key.encode()).hexdigest()[:12]
        return os.path.join(self.cache_dir, f"slide_{slide_index:02d}_{hash_str}.jpg")

    def _is_abstract_topic(self, topic: str) -> bool:
        topic_lower = topic.lower()
        return any(kw in topic_lower for kw in self.AI_GEN_KEYWORDS)

    def _build_query(self, title: str, bullets: list[str]) -> str:
        """Combine title + first bullet into a concise search/generation query."""
        # Strip common filler words
        filler = {"the", "a", "an", "is", "are", "and", "or", "of", "to", "in", "for", "with", "how"}
        words = re.sub(r"[^\w\s]", "", title).split()
        keywords = [w for w in words if w.lower() not in filler][:6]

        if bullets:
            first = re.sub(r"[^\w\s]", "", bullets[0]).split()
            keywords += [w for w in first if w.lower() not in filler][:4]

        return " ".join(keywords[:8]) if keywords else title[:60]

    def _from_pollinations(self, prompt: str, seed: int) -> bytes | None:
        """
        Generate an image via Pollinations.AI — completely free, no key.
        Uses a deterministic seed so the same slide gets the same image.
        """
        try:
            # Make the prompt more visual and presentation-friendly
            enhanced = f"professional presentation illustration of {prompt}, clean minimal style, high quality, no text"
            encoded = requests.utils.quote(enhanced)
            url = self.POLLINATIONS_URL.format(prompt=encoded, seed=seed + 42)

            resp = self._session.get(url, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 5000:
                return resp.content
        except Exception as e:
            print(f"    ⚠  Pollinations error: {e}")
        return None

    def _from_unsplash(self, query: str) -> bytes | None:
        """
        Fetch a random relevant photo from Unsplash.
        Requires a free Unsplash API key set as UNSPLASH_ACCESS_KEY in .env
        Get one free at: https://unsplash.com/developers
        """
        if not UNSPLASH_ACCESS_KEY:
            return None
        try:
            resp = self._session.get(
                self.UNSPLASH_URL,
                params={
                    "query": query,
                    "orientation": "landscape",
                    "content_filter": "high",
                },
                headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
                timeout=10,
            )
            if resp.status_code == 200:
                photo_url = resp.json()["urls"]["regular"]
                img_resp = self._session.get(photo_url, timeout=20)
                if img_resp.status_code == 200:
                    return img_resp.content
        except Exception as e:
            print(f"    ⚠  Unsplash error: {e}")
        return None


# ── Standalone test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    gen = ImageGenerator()

    test_topics = [
        ("artificial intelligence automation", 0),
        ("business analytics data visualization", 1),
        ("team collaboration remote work", 2),
    ]

    print("Testing ImageGenerator...\n")
    for topic, idx in test_topics:
        path = gen.get_image_for_slide(topic, slide_index=idx)
        if path:
            size = os.path.getsize(path) // 1024
            print(f"  ✓ '{topic}' → {path} ({size} KB)")
        else:
            print(f"  ✗ '{topic}' → failed")