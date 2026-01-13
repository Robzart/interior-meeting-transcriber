from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import whisper
import shutil
import uuid
import os
import re

app = FastAPI()

# -------------------------
# Setup
# -------------------------
os.makedirs("uploads", exist_ok=True)

# Load Whisper (CPU, paid Render instance)
model = whisper.load_model("small")

# -------------------------
# Health Check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------
# Rule-based sentence extraction
# -------------------------
def rule_based_extract_notes(transcript: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', transcript.strip())

    def find_sentences(keywords):
        return [
            s.strip()
            for s in sentences
            if any(k.lower() in s.lower() for k in keywords)
        ]

    notes = []

    notes.append("PROJECT OVERVIEW")
    prop = find_sentences(["apartment", "flat", "villa", "house"])
    area = find_sentences(["sq ft", "square feet"])
    family = find_sentences(["family", "kids", "children", "wife"])

    notes.append(f"- Property Type: {prop[0] if prop else 'Not specified'}")
    notes.append(f"- Approx Area: {area[0] if area else 'Not specified'}")
    notes.append(f"- Family Members: {family[0] if family else 'Not specified'}")
    notes.append("")

    notes.append("LIVING ROOM")
    living = find_sentences(
        ["living room", "hall", "tv", "false ceiling", "lighting", "cove"]
    )
    if living:
        for s in living:
            notes.append(f"- {s}")
    else:
        notes.append("- Not specified")
    notes.append("")

    notes.append("KITCHEN")
    kitchen = find_sentences(
        ["kitchen", "modular", "countertop", "drawer", "cabinet", "dishwasher"]
    )
    if kitchen:
        for s in kitchen:
            notes.append(f"- {s}")
    else:
        notes.append("- Not specified")
    notes.append("")

    notes.append("BEDROOMS")
    bedroom = find_sentences(
        ["bedroom", "wardrobe", "study table", "sliding"]
    )
    if bedroom:
        for s in bedroom:
            notes.append(f"- {s}")
    else:
        notes.append("- Not specified")
    notes.append("")

    notes.append("BUDGET / TIMELINE")
    budget = find_sentences(
        ["budget", "cost", "price", "start", "timeline", "march"]
    )
    if budget:
        for s in budget:
            notes.append(f"- {s}")
    else:
        notes.append("- Not specified")

    return "\n".join(notes)

# -------------------------
# Routes
# -------------------------
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
