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

  // START RECORDING
  startBtn.addEventListener("click", async () => {
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recorder = new MediaRecorder(micStream, { mimeType: "audio/mp4" });

      chunks = [];
      recordStartTime = Date.now();

      recorder.ondataavailable = e => {
        if (e.data && e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      recorder.start();
      output.textContent = "🎙 Recording started…";

    } catch (err) {
      output.textContent = "❌ Microphone permission denied.";
    }
  });

  // STOP RECORDING (SAFE VERSION)
  stopBtn.addEventListener("click", () => {
    if (!recorder || !micStream) return;

    if (Date.now() - recordStartTime < 3000) {
      output.textContent = "⚠️ Please record at least 3 seconds.";
      return;
    }

    // 🔴 STOP MIC IMMEDIATELY
    micStream.getTracks().forEach(track => track.stop());
    micStream = null;

    loader.style.display = "block";
    output.textContent = "⏳ Uploading audio…";

    recorder.requestData();

    setTimeout(() => {
      recorder.stop();
    }, 400);
  });

  // WHEN RECORDER FULLY STOPS
  recorderStopped = false;

  const waitForStop = () =>
    new Promise(resolve => recorder.onstop = resolve);

  stopBtn.addEventListener("click", async () => {
    if (!recorder) return;

    await waitForStop();

    try {
      const audioBlob = new Blob(chunks, { type: "audio/mp4" });

      if (!audioBlob || audioBlob.size < 2000) {
        throw new Error("Empty audio");
      }

      const formData = new FormData();
      formData.append("file", audioBlob, "meeting.mp4");

      output.textContent = "🧠 Transcribing audio…";

      const tRes = await fetch("/transcribe", {
        method: "POST",
        body: formData
      });

      if (!tRes.ok) throw new Error("Transcription failed");

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

    } catch (err) {
      loader.style.display = "none";
      output.textContent = "❌ Transcribing failed. Please try again.";
    } finally {
      recorder = null;
      chunks = [];
      recordStartTime = null;
    }
  });

  // DOWNLOAD
  downloadBtn.addEventListener("click", () => {
    if (!window.latestNotes) return;
    const blob = new Blob([window.latestNotes], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "interior-meeting-notes.txt";
    a.click();
  });

  // CLEAR SESSION
  clearBtn.addEventListener("click", () => {
    window.latestNotes = null;
    output.textContent = "Tap “Start Recording” to begin a new meeting.";
  });
});
