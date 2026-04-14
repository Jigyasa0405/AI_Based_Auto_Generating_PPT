import streamlit as st
import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI PowerPoint Generator",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #1A376C 0%, #238BE6 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
    }
    .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; }
    .main-header p { margin: 0.5rem 0 0; opacity: 0.85; font-size: 1rem; }

    .step-card {
        background: #f8faff;
        border: 1px solid #dce8ff;
        border-left: 4px solid #238BE6;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .step-card h4 { margin: 0 0 0.25rem; color: #1A376C; font-size: 0.95rem; }
    .step-card p  { margin: 0; color: #555; font-size: 0.88rem; }

    .success-box {
        background: #efffef;
        border: 1px solid #5cb85c;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        color: #2d6e2d;
    }
    .info-tag {
        background: #e8f0ff;
        color: #1A376C;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 0.15rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎯 AI PowerPoint Generator</h1>
    <p>Upload any document and get a beautifully styled presentation in seconds.</p>
</div>
""", unsafe_allow_html=True)

# ── Supported formats ─────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:1.5rem;">
    <span class="info-tag">📄 PDF</span>
    <span class="info-tag">📝 DOCX</span>
    <span class="info-tag">📋 TXT</span>
    <span class="info-tag">📊 CSV</span>
    <span style="font-size:0.85rem; color:#666; margin-left:0.5rem;">Multiple files supported</span>
</div>
""", unsafe_allow_html=True)

# ── How it works ──────────────────────────────────────────────────────────────
with st.expander("ℹ️ How it works", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="step-card"><h4>Step 1 — Upload</h4><p>Upload one or more documents in supported formats.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="step-card"><h4>Step 2 — AI Analysis</h4><p>LLaMA AI extracts key points and structures them into slides.</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="step-card"><h4>Step 3 — Download</h4><p>Get a styled .pptx file ready to present or edit.</p></div>', unsafe_allow_html=True)

st.divider()

# ── File Upload ───────────────────────────────────────────────────────────────
st.subheader("📁 Upload Document(s)")
uploaded_files = st.file_uploader(
    "Choose file(s)",
    type=["txt", "pdf", "docx", "csv"],
    accept_multiple_files=True,
    help="You can upload multiple files — they'll all be combined into one presentation.",
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
    for f in uploaded_files:
        size_kb = round(len(f.getvalue()) / 1024, 1)
        st.markdown(f"- `{f.name}` — {size_kb} KB")

    # Upload to server
    if len(uploaded_files) == 1:
        file = uploaded_files[0]
        resp = requests.post(f"{BASE_URL}/upload/", files={"file": (file.name, file.getvalue())})
    else:
        files_payload = [("files", (f.name, f.getvalue())) for f in uploaded_files]
        resp = requests.post(f"{BASE_URL}/upload-multiple/", files=files_payload)

    if resp.status_code == 200:
        st.success("✅ File(s) uploaded to server successfully!")
    else:
        st.error(f"❌ Upload failed: {resp.json().get('detail', 'Unknown error')}")
        st.stop()

    st.divider()

    # ── Generate ──────────────────────────────────────────────────────────────
    st.subheader("✨ Generate Presentation")
    st.info("AI will summarize your document(s) and build a styled PowerPoint. This takes ~15–30 seconds.")

    if st.button("🚀 Generate Slides", use_container_width=True, type="primary"):
        with st.spinner("🧠 AI is reading and summarizing your documents..."):
            progress = st.progress(0, text="Extracting text...")
            time.sleep(1)
            progress.progress(25, text="Running AI summarization...")

            gen_resp = requests.get(f"{BASE_URL}/generate/", timeout=180)

            progress.progress(85, text="Building PowerPoint slides...")
            time.sleep(0.5)
            progress.progress(100, text="Done!")

        if gen_resp.status_code == 200:
            data = gen_resp.json()
            st.markdown("""
<div class="success-box">
    <strong>🎉 Presentation generated successfully!</strong><br>
    Your styled PowerPoint is ready to download.
</div>
""", unsafe_allow_html=True)
            st.write("")

            # Download button
            dl_resp = requests.get(f"{BASE_URL}/download/", timeout=30)
            if dl_resp.status_code == 200:
                st.download_button(
                    label="⬇️ Download PowerPoint (.pptx)",
                    data=dl_resp.content,
                    file_name="AI_Presentation.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True,
                )
            else:
                st.error("Could not fetch the file for download. Try the /download/ API endpoint directly.")
        else:
            detail = gen_resp.json().get("detail", "Unknown error")
            st.error(f"❌ Generation failed: {detail}")
            st.write("Check that your `GROQ_API_KEY` is set correctly in `.env`")

else:
    st.markdown("""
    <div style="text-align:center; padding:3rem 1rem; color:#aaa; border:2px dashed #dce8ff; border-radius:12px;">
        <div style="font-size:3rem;">📂</div>
        <div style="margin-top:0.5rem;">Upload a document above to get started</div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#bbb; font-size:0.8rem;'>Powered by LLaMA 3.3 via Groq · HuggingFace Embeddings · python-pptx</p>",
    unsafe_allow_html=True,
)