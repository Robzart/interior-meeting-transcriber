from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import whisper
import shutil
import uuid
import os

app = FastAPI()

# Ensure uploads folder exists
os.makedirs("uploads", exist_ok=True)

# Load Whisper model (already working in your setup)
model = whisper.load_model("small")

# -------------------------------
# Rule-based note extraction
# -------------------------------
def rule_based_extract_notes(transcript: str) -> str:
    text = transcript.lower()

    def has(words):
        return any(w in text for w in words)

    notes = []

    notes.append("PROJECT OVERVIEW")
    notes.append(f"- Property Type: {'Mentioned' if has(['flat', 'apartment', 'villa', 'house']) else 'Not specified'}")
    notes.append(f"- Approx Area: {'Mentioned' if has(['sq ft', 'square feet']) else 'Not specified'}")
    notes.append(f"- Family Members: {'Mentioned' if has(['family', 'kids', 'children']) else 'Not specified'}")
    notes.append("")

    notes.append("LIVING ROOM")
    if has(['living room', 'hall']):
        if has(['tv unit', 'television']):
            notes.append("- TV unit discussed")
        if has(['false ceiling', 'ceiling']):
            notes.append("- False ceiling mentioned")
        if has(['lighting', 'cove', 'led']):
            notes.append("- Lighting discussed")
    else:
        notes.append("- Not specified")
    notes.append("")

    notes.append("KITCHEN")
    if has(['kitchen']):
        if has(['modular']):
            notes.append("- Modular kitchen mentioned")
        if has(['quartz', 'granite', 'countertop']):
            notes.append("- Countertop material discussed")
        if has(['drawer', 'cabinet']):
            notes.append("- Storage discussed")
    else:
        notes.append("- Not specified")
    notes.append("")

    notes.append("BEDROOMS")
    if has(['bedroom']):
        if has(['wardrobe']):
            notes.append("- Wardrobe discussed")
        if has(['study table', 'work desk']):
            notes.append("- Study table mentioned")
    else:
        notes.append("- Not specified")
    notes.append("")

    notes.append("BUDGET / TIMELINE")
    if has(['budget', 'cost', 'price']):
        notes.append("- Budget discussion present")
    else:
        notes.append("- Not specified")

    return "\n".join(notes)

# -------------------------------
# Routes
# -------------------------------
@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    filename = f"uploads/{uuid.uuid4()}.mp4"

    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = model.transcribe(filename)
    return {"text": result["text"]}

@app.post("/extract-notes")
async def extract_notes(payload: dict):
    transcript = payload.get("transcript", "").strip()
    notes = rule_based_extract_notes(transcript)
    return {"notes": notes}
