import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from src.agents.pipeline import PipelineAgent

router = APIRouter()

UPLOAD_DIR = "uploads/"
OUTPUT_DIR = "output/"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".csv"}


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported type '{ext}'. Supported: {SUPPORTED_EXTENSIONS}")
    for f in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, f))
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "message": "File uploaded successfully!"}


@router.post("/upload-multiple/")
async def upload_multiple_files(files: list[UploadFile] = File(...)):
    for f in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, f))
    uploaded = []
    for file in files:
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in SUPPORTED_EXTENSIONS:
            continue
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded.append(file.filename)
    if not uploaded:
        raise HTTPException(400, "No supported files found in upload.")
    return {"uploaded": uploaded, "message": f"{len(uploaded)} file(s) uploaded!"}


@router.get("/generate/")
async def generate_presentation(
    enable_images: bool = Query(default=True, description="Fetch images for slides")
):
    """Run the full AI pipeline. Pass ?enable_images=false to skip image fetching."""
    uploads = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
    if not uploads:
        raise HTTPException(400, "No files uploaded. Please upload files first.")
    try:
        agent = PipelineAgent(output_dir=OUTPUT_DIR, enable_images=enable_images)
        pptx_path = agent.run_from_directory(UPLOAD_DIR)
        filename  = os.path.basename(pptx_path)
        return {
            "message": "Slides generated successfully!",
            "download_url": f"/download/?filename={filename}",
            "filename": filename,
            "images_used": enable_images,
        }
    except Exception as e:
        raise HTTPException(500, f"Slide generation failed: {str(e)}")


@router.get("/download/")
async def download_presentation(filename: str = "generated_presentation.pptx"):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(404, "Presentation not found. Generate it first.")
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename="AI_Presentation.pptx",
    )


@router.get("/status/")
async def status():
    uploads     = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
    pptx_exists = os.path.exists(os.path.join(OUTPUT_DIR, "generated_presentation.pptx"))
    return {"uploaded_files": uploads, "presentation_ready": pptx_exists}