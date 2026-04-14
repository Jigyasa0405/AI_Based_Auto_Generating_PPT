# AI-Based Auto-Generating PowerPoint Slides

An agentic AI pipeline that reads any document (PDF, DOCX, TXT, CSV) and automatically generates a visually styled PowerPoint presentation — complete with AI-summarised bullet points and relevant images.

---

## Features

- **Multi-format support** — PDF, DOCX, TXT, CSV
- **AI summarisation** — LLaMA 3.3 via Groq extracts key slide-ready points
- **Structured output** — AI returns JSON with titles, bullets, theme colour, and speaker notes
- **Visual slides** — Themed colour palettes, styled headers, cover and conclusion slides
- **Image embedding** — Pollinations.AI (free, no key) or Unsplash (free key) adds images to content slides
- **Image caching** — Downloaded images are cached locally so repeated runs are fast
- **REST API** — FastAPI backend with upload, generate, and download endpoints
- **Web UI** — Streamlit frontend with progress tracking and one-click download
- **100% free** — No paid API keys required

---

## Project Structure

```
AI_Based_Auto_Generating_PPT/
│
├── src/
│   ├── agents/
│   │   ├── content_extractor.py   # Extracts text from files
│   │   ├── summarizer.py          # AI summarisation → structured JSON
│   │   ├── image_generator.py     # Fetches/generates slide images (free)
│   │   ├── slide_generator.py     # Builds styled .pptx with python-pptx
│   │   └── pipeline.py            # Orchestrator agent chaining all steps
│   │
│   ├── api/
│   │   ├── main.py                # FastAPI app entry point
│   │   └── routes.py              # Upload / generate / download endpoints
│   │
│   └── ui/
│       └── app.py                 # Streamlit web interface
│
├── data/                          # Put sample input files here
├── output/                        # Generated .pptx saved here (git-ignored)
├── uploads/                       # Temp upload storage (git-ignored)
│
├── .env.example                   # Template for environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AI_Based_Auto_Generating_PPT.git
cd AI_Based_Auto_Generating_PPT
```

### 2. Create and activate a Conda environment

```bash
conda create -n auto_gen_ppt python=3.10
conda activate auto_gen_ppt
```

Or with venv:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The first run will download the HuggingFace embedding model (~130 MB). This is cached automatically and only happens once.

### 4. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
GROQ_API_KEY=your_groq_api_key_here        # required
UNSPLASH_ACCESS_KEY=your_unsplash_key_here  # optional
```

**Getting a free Groq API key:**
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Navigate to **API Keys** → **Create API Key**
4. Paste it into `.env`

**Getting a free Unsplash key (optional — improves photo quality):**
1. Go to [unsplash.com/developers](https://unsplash.com/developers)
2. Click **Register as a developer** (free)
3. Create a new application
4. Copy the **Access Key** into `.env`

---

## Running the App

You need **two terminals** running simultaneously.

### Terminal 1 — Start the FastAPI backend

```bash
conda activate auto_gen_ppt
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at: `http://127.0.0.1:8000`  
Interactive API docs: `http://127.0.0.1:8000/docs`

### Terminal 2 — Start the Streamlit frontend

```bash
conda activate auto_gen_ppt
streamlit run src/ui/app.py
```

The UI will open automatically at: `http://localhost:8501`

---

## Using the Web UI

1. Open `http://localhost:8501` in your browser
2. Upload one or more documents (PDF, DOCX, TXT, or CSV)
3. Click **Generate Slides**
4. Wait ~20–40 seconds for AI processing
5. Click **Download PowerPoint** to save your `.pptx`

---

## Running Agents Standalone

Each agent can be tested independently:

```bash
# Test content extraction
python src/agents/content_extractor.py

# Test AI summarisation
python src/agents/summarizer.py

# Test image fetching
python src/agents/image_generator.py

# Test slide generation (with images)
python src/agents/slide_generator.py

# Run the full pipeline on the data/ folder
python src/agents/pipeline.py
```

---

## How the AI Pipeline Works

```
┌─────────────────┐
│  Input Document │  PDF / DOCX / TXT / CSV
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  ContentExtractor   │  Reads and cleans raw text
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│     Summarizer      │  LLaMA 3.3 via Groq
│                     │  Returns structured JSON:
│  - presentation_title    title, subtitle, theme
│  - slides[]              per-slide: title, bullets,
│  - theme_color           slide_type, speaker_note
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   ImageGenerator    │  Pollinations.AI (free, no key)
│                     │  or Unsplash (free key, optional)
│  - Picks source by topic  Cached in output/slide_images/
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   SlideGenerator    │  python-pptx
│                     │  Cover slide + themed content slides
│  - Split layout if image available    + conclusion slide
│  - Full-width layout otherwise        + speaker notes
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  output/*.pptx      │  Ready to present or edit
└─────────────────────┘
```

---

## Available Themes

The AI automatically picks a theme based on document content. Available themes: `blue`, `green`, `purple`, `orange`, `red`, `teal`.

---

## Tech Stack

| Component | Library | Cost |
|-----------|---------|------|
| LLM (summarisation) | LLaMA 3.3 70B via [Groq](https://groq.com) | Free tier |
| Embeddings | `BAAI/bge-small-en-v1.5` via HuggingFace | Free, local |
| RAG / indexing | LlamaIndex | Open source |
| Image generation | [Pollinations.AI](https://pollinations.ai) | Free, no key |
| Stock photos | [Unsplash API](https://unsplash.com/developers) | Free tier |
| Slide building | `python-pptx` | Open source |
| API | FastAPI + Uvicorn | Open source |
| UI | Streamlit | Open source |

---

## License

MIT License — feel free to use, modify, and distribute.
