document.addEventListener("DOMContentLoaded", () => {
  let recorder = null;
  let micStream = null;
  let chunks = [];
  let recordStartTime = null;

  const startBtn = document.getElementById("start");
  const stopBtn = document.getElementById("stop");
  const downloadBtn = document.getElementById("download");
  const clearBtn = document.getElementById("clear");
  const output = document.getElementById("output");
  const statusDiv = document.getElementById("status");
  const loader = document.getElementById("loader");

  // App health
  fetch("/health")
    .then(() => {
      statusDiv.textContent = "🟢 App Status: Live";
      statusDiv.style.background = "#e6f4ea";
    })
    .catch(() => {
      statusDiv.textContent = "🔴 App Status: Offline";
      statusDiv.style.background = "#fdecea";
    });

  // Start recording
  startBtn.addEventListener("click", async () => {
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recorder = new MediaRecorder(micStream, { mimeType: "audio/mp4" });

      chunks = [];
      recordStartTime = Date.now();

      recorder.ondataavailable = e => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.start();
      output.textContent = "🎙 Recording started…";

    } catch {
      output.textContent = "❌ Microphone permission denied.";
    }
  });

  // Stop recording — HARD mic stop
  stopBtn.addEventListener("click", () => {
    if (!recorder || !micStream) return;

    if (Date.now() - recordStartTime < 3000) {
      output.textContent = "⚠️ Please record at least 3 seconds.";
      return;
    }

    // 🔴 STOP MIC IMMEDIATELY (KEY FIX)
    micStream.getTracks().forEach(track => track.stop());
    micStream = null;

    loader.style.display = "block";
    output.textContent = "⏳ Uploading audio…";

    recorder.requestData();
    setTimeout(() => recorder.stop(), 300);
  });

  // After recording stops
  recorderStopHandler = async () => {};

  document.addEventListener("recorderStop", async () => {
    try {
      const audioBlob = new Blob(chunks, { type: "audio/mp4" });
      const formData = new FormData();
      formData.append("file", audioBlob, "meeting.mp4");

      output.textContent = "🧠 Transcribing audio…";
      const tRes = await fetch("/transcribe", { method: "POST", body: formData });
      const tData = await tRes.json();

      output.textContent = "📝 Structuring meeting notes…";
      const nRes = await fetch("/extract-notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: tData.text })
      });

      const nData = await nRes.json();
      window.latestNotes = nData.notes;

      loader.style.display = "none";
      output.textContent = "📝 MEETING NOTES\n\n" + nData.notes;

    } catch {
      loader.style.display = "none";
      output.textContent = "❌ Processing failed.";
    } finally {
      recorder = null;
      chunks = [];
      recordStartTime = null;
    }
  });

  // Recorder stop hook
  const originalStop = MediaRecorder.prototype.stop;
  MediaRecorder.prototype.stop = function () {
    originalStop.call(this);
    document.dispatchEvent(new Event("recorderStop"));
  };

  // Download
  downloadBtn.addEventListener("click", () => {
    if (!window.latestNotes) return;
    const blob = new Blob([window.latestNotes], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "interior-meeting-notes.txt";
    a.click();
  });

  // Clear session
  clearBtn.addEventListener("click", () => {
    window.latestNotes = null;
    output.textContent = "Tap “Start Recording” to begin a new meeting.";
  });
});
