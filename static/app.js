document.addEventListener("DOMContentLoaded", () => {
  let recorder = null;
  let chunks = [];
  let recordStartTime = null;

  const startBtn = document.getElementById("start");
  const stopBtn = document.getElementById("stop");
  const downloadBtn = document.getElementById("download");
  const output = document.getElementById("output");
  const statusDiv = document.getElementById("status");
  const loader = document.getElementById("loader");

  // -------------------------
  // App status
  // -------------------------
  fetch("/health")
    .then(() => {
      statusDiv.textContent = "🟢 App Status: Live";
      statusDiv.style.background = "#e6f4ea";
    })
    .catch(() => {
      statusDiv.textContent = "🔴 App Status: Offline";
      statusDiv.style.background = "#fdecea";
    });

  // -------------------------
  // Start recording
  // -------------------------
  startBtn.addEventListener("click", async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      recorder = new MediaRecorder(stream, { mimeType: "audio/mp4" });
      chunks = [];
      recordStartTime = Date.now();

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.start();
      output.textContent = "🎙 Recording started… Speak clearly.";

    } catch (err) {
      output.textContent = "❌ Microphone access denied.";
    }
  });

  // -------------------------
  // Stop recording
  // -------------------------
  stopBtn.addEventListener("click", () => {
    if (!recorder) return;

    if (Date.now() - recordStartTime < 3000) {
      output.textContent = "⚠️ Please record at least 3 seconds.";
      return;
    }

    loader.style.display = "block";
    output.textContent = "⏳ Uploading audio…";

    recorder.requestData();
    setTimeout(() => recorder.stop(), 500);

    recorder.onstop = async () => {
      try {
        const audioBlob = new Blob(chunks, { type: "audio/mp4" });

        const formData = new FormData();
        formData.append("file", audioBlob, "meeting.mp4");

        output.textContent = "🧠 Transcribing audio…";

        const tRes = await fetch("/transcribe", {
          method: "POST",
          body: formData
        });
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
    };
  });

  // -------------------------
  // Download notes
  // -------------------------
  downloadBtn.addEventListener("click", () => {
    if (!window.latestNotes) return;

    const blob = new Blob([window.latestNotes], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "interior-meeting-notes.txt";
    a.click();

    URL.revokeObjectURL(url);
  });
});
