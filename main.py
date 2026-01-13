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

model = whisper.load_model("small")

# -------------------------
# Health Check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------
# Professional rule-based extraction
# -------------------------
def rule_based_extract_notes(transcript: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', transcript.strip())

    def clean(s):
        return s.strip().capitalize()

    def find(keywords):
        return [
            clean(s) for s in sentences
            if not s.strip().endswith("?")
            and any(k in s.lower() for k in keywords)
        ]

    notes = []

    # PROJECT OVERVIEW
    notes.append("PROJECT OVERVIEW")
    prop = find(["3 bhk", "apartment", "flat", "villa", "house"])
    area = find(["sq ft", "square feet"])
    family = find(["wife", "kids", "children", "family"])

    notes.append(f"- Property Type: {prop[0] if prop else 'Not specified'}")
    notes.append(f"- Area: {area[0] if area else 'Not specified'}")
    notes.append(f"- Family Members: {family[0] if family else 'Not specified'}")
    notes.append("")

    # LIVING ROOM
    notes.append("LIVING ROOM")
    tv = find(["tv unit"])
    ceiling = find(["false ceiling"])
    lighting = find(["lighting", "cove", "warm"])

    if tv:
        notes.append(f"- TV Unit: {tv[0]}")
    if ceiling:
        notes.append(f"- Ceiling: {ceiling[0]}")
    if lighting:
        notes.append(f"- Lighting: {lighting[0]}")
    if not (tv or ceiling or lighting):
        notes.append("- Not specified")
    notes.append("")

    # KITCHEN
    notes.append("KITCHEN")
    modular = find(["modular kitchen"])
    counter = find(["quartz", "granite", "countertop"])
    storage = find(["drawer", "soft close", "cabinet"])
    appliance = find(["dishwasher", "microwave"])

    if modular:
        notes.append("- Type: Modular kitchen")
    if counter:
        notes.append(f"- Countertop: {counter[0]}")
    if storage:
        notes.append("- Storage: Soft-close drawers")
    if appliance:
        notes.append("- Appliances: Dishwasher / microwave space required")
    if not (modular or counter or storage or appliance):
        notes.append("- Not specified")
    notes.append("")

    # MASTER BEDROOM
    notes.append("MASTER BEDROOM")
    wardrobe = find(["wardrobe", "sliding"])
    study = find(["study table"])
    colour = find(["colour", "neutral"])

    if wardrobe:
        notes.append(f"- Wardrobe: {wardrobe[0]}")
    if study:
        notes.append(f"- Study Table: {study[0]}")
    if colour:
        notes.append(f"- Colour Preference: {colour[0]}")
    if not (wardrobe or study or colour):
        notes.append("- Not specified")
    notes.append("")

    # BUDGET & TIMELINE
    notes.append("BUDGET & TIMELINE")
    budget = find(["budget"])
    timeline = find(["march", "april", "start", "timeline"])

    if budget:
        notes.append(f"- Budget: {budget[0]}")
    if timeline:
        notes.append(f"- Timeline: {timeline[0]}")
    if not (budget or timeline):
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
