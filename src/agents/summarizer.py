import os
import json
import re
from dotenv import load_dotenv
from llama_index.core import GPTVectorStoreIndex, Document
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.settings import Settings

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


STRUCTURED_PROMPT = """
Analyze the following text and create a structured PowerPoint presentation outline.

Return ONLY a valid JSON object in this exact format (no extra text, no markdown):
{
  "presentation_title": "A concise, catchy title for the presentation",
  "subtitle": "A short subtitle or tagline",
  "theme_color": "Choose ONE: blue | green | purple | orange | red | teal",
  "slides": [
    {
      "slide_title": "Slide heading (max 8 words)",
      "slide_type": "intro | content | data | quote | conclusion",
      "bullet_points": [
        "First key point (concise, max 15 words)",
        "Second key point",
        "Third key point"
      ],
      "speaker_note": "One sentence summarizing what to say on this slide"
    }
  ]
}

Rules:
- Generate 5 to 8 slides total
- First slide should be an 'intro' type with 2-3 bullet points giving an overview
- Last slide should be a 'conclusion' type with key takeaways
- Each content slide should have 3-5 bullet points
- Bullet points must be clear, informative, and presentation-ready
- Do NOT include any text outside the JSON object
"""


class Summarizer:
    def __init__(self):
        Settings.llm = Groq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def summarize_text(self, text: str) -> dict:
        """Summarizes text and returns structured slide data as a dict."""
        # Truncate very long texts to avoid token limits
        max_chars = 6000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Content truncated for processing]"

        full_prompt = f"{STRUCTURED_PROMPT}\n\nTEXT TO ANALYZE:\n{text}"

        documents = [Document(text=full_prompt)]
        index = GPTVectorStoreIndex.from_documents(documents)
        query_engine = index.as_query_engine(similarity_top_k=1)

        response = query_engine.query(
            "Generate the structured JSON presentation outline as instructed."
        )

        raw = response.response.strip()
        return self._parse_response(raw, text)

    def _parse_response(self, raw: str, original_text: str) -> dict:
        """Parse JSON from LLM response, with fallback."""
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        raw = raw.strip()

        # Find JSON object
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                # Validate required keys
                if "slides" in data and "presentation_title" in data:
                    return data
            except json.JSONDecodeError:
                pass

        # Fallback: build a minimal structure from raw text
        print("  ⚠ Could not parse structured JSON, using fallback structure.")
        lines = [l.strip() for l in raw.split("\n") if l.strip()]
        bullets = [l.lstrip("-•*123456789. ") for l in lines if len(l) > 10][:15]

        return {
            "presentation_title": "AI-Generated Presentation",
            "subtitle": "Auto-generated from document",
            "theme_color": "blue",
            "slides": [
                {
                    "slide_title": "Overview",
                    "slide_type": "intro",
                    "bullet_points": bullets[:4] or ["Content extracted from document"],
                    "speaker_note": "Introduction to the topic.",
                },
                {
                    "slide_title": "Key Points",
                    "slide_type": "content",
                    "bullet_points": bullets[4:9] or ["See document for details"],
                    "speaker_note": "Main content of the presentation.",
                },
                {
                    "slide_title": "Conclusion",
                    "slide_type": "conclusion",
                    "bullet_points": bullets[9:13] or ["Thank you for your attention"],
                    "speaker_note": "Summary and closing remarks.",
                },
            ],
        }


if __name__ == "__main__":
    sample_text = """
    AI is transforming industries by automating repetitive tasks and enabling data-driven decision-making.
    Machine learning models can now process vast amounts of data in real time.
    Natural Language Processing allows computers to understand and generate human language.
    Computer vision enables machines to interpret and understand visual information.
    This project aims to generate PowerPoint slides automatically from input documents.
    It extracts text from PDFs, DOCX, TXT, and CSV files, then converts them into structured slides.
    The AI pipeline uses Groq LLaMA for text summarization and LlamaIndex for retrieval.
    Benefits include saving hours of manual slide creation and ensuring consistent formatting.
    """

    summarizer = Summarizer()
    result = summarizer.summarize_text(sample_text)

    print("\n✅ Structured Output:")
    print(json.dumps(result, indent=2))