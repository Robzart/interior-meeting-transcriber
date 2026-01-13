document.addEventListener("DOMContentLoaded", () => {
  let recorder = null;
  let chunks = [];
  let recordStartTime = null;

  const startBtn = document.getElementById("start");
  const stopBtn = document.getElementById("stop");
  const downloadBtn = document.getElementById("download");
  const output = document.getElementById("output");
  const statusDiv = document.getElementById("status");

  // -------------------------
  // App status check
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
      console.error(err);
      output.textContent =
        "❌ Microphone access failed. Please allow mic permission.";
    }
  });

  // -------------------------
  // Stop recording (Safari-safe)
  // -------------------------
  stopBtn.addEventListener("click", () => {
    if (!recorder) {
      output.textContent = "⚠️ Recorder not active.";
      return;
    }

    const duration = Date.now() - recordStartTime;

    if (duration < 3000) {
      output.textContent =
        "⚠️ Please record at least 3 seconds before stopping.";
      return;
    }

    output.textContent = "⏳ Uploading audio…";

    recorder.requestData();

    setTimeout(() => {
      recorder.stop();
    }, 500);

    recorder.onstop = async () => {
      try {
        const audioBlob = new Blob(chunks, { type: "audio/mp4" });

        if (audioBlob.size < 3000) {
          output.textContent = "❌ Recording failed. Please try again.";
          return;
        }

        const formData = new FormData();
        formData.append("file", audioBlob, "meeting.mp4");

        output.textContent =
          "🧠 Transcribing audio… This may take up to 1 minute.";

        const response = await fetch("/transcribe", {
          method: "POST",
          body: formData
        });

        const data = await response.json();

        output.textContent = "📝 Generating structured meeting notes…";

        const notesResponse = await fetch("/extract-notes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcript: data.text })
        });

        const notesData = await notesResponse.json();
        window.latestNotes = notesData.notes;

        output.textContent =
          "📝 MEETING NOTES\n\n" + notesData.notes;

      } catch (err) {
        console.error(err);
        output.textContent =
          "❌ Error processing recording. Please try again.";
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
    if (!window.latestNotes) {
      alert("No notes available to download yet.");
      return;
    }

    const blob = new Blob([window.latestNotes], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "interior-meeting-notes.txt";
    a.click();

    URL.revokeObjectURL(url);
  });
});
