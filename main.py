from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import whisper
import shutil
import uuid
import os

app = FastAPI()

# -------------------------
# Setup
# -------------------------
os.makedirs("uploads", exist_ok=True)
model = whisper.load_model("small")

# -------------------------
# Health check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------
# Helper for field extraction
# -------------------------
def extract_value(transcript: str, keywords):
    for line in transcript.split("."):
        l = line.lower()
        if any(k in l for k in keywords):
            cleaned = line.strip()
            for w in ["yes", "okay", "alright", "so", "then"]:
                cleaned = cleaned.replace(w.capitalize(), "").replace(w, "")
            return cleaned.strip()
    return "Not specified"

# -------------------------
# Rule-based structured notes
# -------------------------
def rule_based_extract_notes(transcript: str) -> str:
    notes = []

    # PROJECT OVERVIEW
    notes.append("PROJECT OVERVIEW")
    notes.append(f"- Property Type: {extract_value(transcript, ['3 bhk', 'apartment', 'flat', 'villa'])}")
    notes.append(f"- Area: {extract_value(transcript, ['square feet', 'sq ft'])}")
    notes.append(f"- Family Members: {extract_value(transcript, ['wife', 'kids', 'children', 'family'])}")
    notes.append("")

    # LIVING ROOM
    notes.append("LIVING ROOM")
    notes.append(f"- TV Unit: {extract_value(transcript, ['tv unit'])}")
    notes.append(f"- Ceiling: {extract_value(transcript, ['false ceiling'])}")
    notes.append(f"- Lighting: {extract_value(transcript, ['cove', 'warm light', 'led'])}")
    notes.append("")

    # KITCHEN
    notes.append("KITCHEN")
    notes.append(f"- Type: {extract_value(transcript, ['modular kitchen'])}")
    notes.append(f"- Countertop: {extract_value(transcript, ['quartz', 'granite', 'countertop'])}")
    notes.append(f"- Storage: {extract_value(transcript, ['soft close', 'drawer', 'cabinet'])}")
    notes.append(f"- Appliances: {extract_value(transcript, ['dishwasher', 'microwave'])}")
    notes.append("")

    # MASTER BEDROOM
    notes.append("MASTER BEDROOM")
    notes.append(f"- Wardrobe: {extract_value(transcript, ['wardrobe'])}")
    notes.append(f"- Study Table: {extract_value(transcript, ['study table'])}")
    notes.append(f"- Colour Preference: {extract_value(transcript, ['colour', 'neutral', 'walnut'])}")
    notes.append("")

    # BATHROOMS
    notes.append("BATHROOMS")
    notes.append(f"- Fittings: {extract_value(transcript, ['bathroom fittings', 'fittings'])}")
    notes.append(f"- Tiles: {extract_value(transcript, ['tiles', 'wall tiles', 'floor tiles'])}")
    notes.append(f"- Storage: {extract_value(transcript, ['vanity', 'mirror cabinet'])}")
    notes.append("")

    # BALCONY
    notes.append("BALCONY")
    notes.append(f"- Usage: {extract_value(transcript, ['balcony'])}")
    notes.append(f"- Flooring: {extract_value(transcript, ['outdoor tiles', 'deck', 'artificial grass'])}")
    notes.append("")

    # ELECTRICAL & LIGHTING
    notes.append("ELECTRICAL & LIGHTING")
    notes.append(f"- Switches & Points: {extract_value(transcript, ['switch', 'socket', 'plug point'])}")
    notes.append(f"- Special Lighting: {extract_value(transcript, ['profile light', 'spotlight', 'sensor'])}")
    notes.append("")

    # BUDGET & TIMELINE
    notes.append("BUDGET & TIMELINE")
    notes.append(f"- Budget: {extract_value(transcript, ['budget', 'lakhs'])}")
    notes.append(f"- Timeline: {extract_value(transcript, ['start', 'march', 'april', 'may'])}")

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

    # 🔐 Delete audio immediately
    os.remove(filename)

    return {"text": result["text"]}

@app.post("/extract-notes")
async def extract_notes(payload: dict):
    transcript = payload.get("transcript", "").strip()
    notes = rule_based_extract_notes(transcript)
    return {"notes": notes}
