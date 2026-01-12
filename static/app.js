let recorder = null;
let chunks = [];

const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");
const output = document.getElementById("output");

/**
 * START RECORDING
 */
startBtn.addEventListener("click", async () => {
  try {
    // Request mic access (Safari-safe)
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // iOS Safari compatible format
    recorder = new MediaRecorder(stream, {
      mimeType: "audio/mp4"
    });

    chunks = [];

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        chunks.push(e.data);
      }
    };

    recorder.start();

    output.textContent = "🎙 Recording started...\nSpeak clearly.";

  } catch (err) {
    console.error(err);
    output.textContent =
      "❌ Microphone access failed.\nPlease allow mic permission in Safari settings.";
  }
});

/**
 * STOP RECORDING & UPLOAD
 */
stopBtn.addEventListener("click", async () => {
  if (!recorder) {
    output.textContent = "⚠️ Recorder not initialized.";
    return;
  }

  // Force Safari to flush last audio chunk
  recorder.requestData();
  recorder.stop();

  output.textContent = "⏹ Recording stopped.\nPreparing audio...";

  recorder.onstop = async () => {
    try {
      const audioBlob = new Blob(chunks, { type: "audio/mp4" });

      // Basic validation
      if (audioBlob.size < 1000) {
        output.textContent =
          "❌ Recording too short or failed.\nPlease try again.";
        return;
      }

      output.textContent =
        `🎧 Audio captured (${Math.round(audioBlob.size / 1024)} KB)\nUploading...`;

      const formData = new FormData();
      formData.append("file", audioBlob, "meeting.mp4");

      const response = await fetch("/transcribe", {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        throw new Error("Server error during transcription");
      }

      const data = await response.json();

      output.textContent =
        "✅ Transcription complete:\n\n" + (data.text || "(No text detected)");

    } catch (err) {
      console.error(err);
      output.textContent =
        "❌ Error processing audio.\nPlease check network and try again.";
    } finally {
      recorder = null;
      chunks = [];
    }
  };
});
