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
# Health check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------
# Utility helpers
# -------------------------
def normalize(text: str) -> str:
    text = text.lower()

    remove_phrases = [
        "yes", "okay", "alright", "sure", "we want", "we need",
        "this will be", "it is", "it's", "should be", "around",
        "approximately", "please", "also", "so"
    ]

    for r in remove_phrases:
        text = text.replace(r, "")

    return text.strip().capitalize()


def extract_value(transcript: str, keywords, patterns=None):
    sentences = transcript.split(".")
    for s in sentences:
        s_low = s.lower()
        if any(k in s_low for k in keywords):
            if patterns:
                for p in patterns:
                    m = re.search(p, s_low)
                    if m:
                        return m.group(1).capitalize()
            return normalize(s)
    return "Not specified"

# -------------------------
# Structured rule-based notes
# -------------------------
def rule_based_extract_notes(transcript: str) -> str:
    notes = []

    # PROJECT OVERVIEW
    notes.append("PROJECT OVERVIEW")
    notes.append("- Property Type: " + extract_value(
        transcript, ["3 bhk", "apartment", "flat", "villa"]
    ))
    notes.append("- Area: " + extract_value(
        transcript, ["sq ft", "square feet"],
        [r"(\d+\s*(?:sq ft|square feet))"]
    ))
    notes.append("- Family Members: " + extract_value(
        transcript, ["wife", "kids", "children", "family"]
    ))
    notes.append("")

    # LIVING ROOM
    notes.append("LIVING ROOM")
    notes.append("- TV Unit: " + extract_value(
        transcript, ["tv unit"],
        [r"(east|west|north|south)[-\s]facing wall"]
    ))
    notes.append("- Ceiling: " + extract_value(
        transcript, ["false ceiling"]
    ))
    notes.append("- Lighting: " + extract_value(
        transcript, ["cove", "warm"],
        [r"warm\s+\w+"]
    ))
    notes.append("")

    # KITCHEN
    notes.append("KITCHEN")
    notes.append("- Type: " + extract_value(
        transcript, ["modular kitchen"],
        [r"modular kitchen"]
    ))
    notes.append("- Countertop: " + extract_value(
        transcript, ["quartz", "granite"]
    ))
    notes.append("- Storage: " + extract_value(
        transcript, ["soft close", "drawer"],
        [r"soft[-\s]close drawers"]
    ))
    notes.append("- Appliances: " + extract_value(
        transcript, ["dishwasher", "microwave"]
    ))
    notes.append("")

    # MASTER BEDROOM
    notes.append("MASTER BEDROOM")
    notes.append("- Wardrobe: " + extract_value(
        transcript, ["wardrobe"],
        [r"(\d+\s*feet wide)"]
    ))
    notes.append("- Study Table: " + extract_value(
        transcript, ["study table"]
    ))
    notes.append("- Colour Preference: " + extract_value(
        transcript, ["neutral", "walnut", "beige", "grey"]
    ))
    notes.append("")

    # BATHROOMS
    notes.append("BATHROOMS")
    notes.append("- Fittings: " + extract_value(
        transcript, ["wall mounted"]
    ))
    notes.append("- Tiles: " + extract_value(
        transcript, ["tiles", "large format"]
    ))
    notes.append("- Storage: " + extract_value(
        transcript, ["vanity", "mirror cabinet"]
    ))
    notes.append("")

    # BALCONY
    notes.append("BALCONY")
    notes.append("- Usage: " + extract_value(
        transcript, ["balcony", "sit out", "sit-out"]
    ))
    notes.append("- Flooring: " + extract_value(
        transcript, ["outdoor tiles", "deck"]
    ))
    notes.append("")

    # ELECTRICAL
    notes.append("ELECTRICAL & LIGHTING")
    notes.append("- Switches & Points: " + extract_value(
        transcript, ["plug point", "socket"]
    ))
    notes.append("- Special Lighting: " + extract_value(
        transcript, ["profile", "spot", "sensor"]
    ))
    notes.append("")

    # BUDGET & TIMELINE
    notes.append("BUDGET & TIMELINE")
    notes.append("- Budget: " + extract_value(
        transcript, ["lakhs"],
        [r"\d+\s*lakhs"]
    ))
    notes.append("- Timeline: " + extract_value(
        transcript, ["march", "april", "may", "june"]
    ))

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

    # Privacy-safe cleanup
    os.remove(filename)

    return {"text": result["text"]}

@app.post("/extract-notes")
async def extract_notes(payload: dict):
    transcript = payload.get("transcript", "")
    notes = rule_based_extract_notes(transcript)
    return {"notes": notes}
