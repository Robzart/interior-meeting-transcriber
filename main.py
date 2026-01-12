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

# Load Whisper model
model = whisper.load_model("base")

# Serve static frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    filename = f"uploads/{uuid.uuid4()}.mp4"

    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = model.transcribe(filename)
    return {"text": result["text"]}
