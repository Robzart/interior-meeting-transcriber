document.addEventListener("DOMContentLoaded", () => {
  let recorder = null;
  let chunks = [];
  let recordStartTime = null;

  const startBtn = document.getElementById("start");
  const stopBtn = document.getElementById("stop");
  const output = document.getElementById("output");

  if (!startBtn || !stopBtn || !output) {
    console.error("Required HTML elements not found");
    return;
  }

  /* =========================
     START RECORDING
     ========================= */
  startBtn.addEventListener("click", async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      recorder = new MediaRecorder(stream, {
        mimeType: "audio/mp4" // Safari compatible
      });

      chunks = [];
      recordStartTime = Date.now(); // ✅ REQUIRED FOR SAFARI

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

  /* =========================
     STOP RECORDING (SAFARI-SAFE)
     ========================= */
  stopBtn.addEventListener("click", () => {
    if (!recorder) {
      output.textContent = "⚠️ Recorder not active.";
      return;
    }

    const duration = Date.now() - recordStartTime;

    // ✅ Safari requires minimum recording time
    if (duration < 3000) {
      output.textContent =
        "⚠️ Please record at least 3 seconds before stopping.";
      return;
    }

    output.textContent = "⏹ Stopping recording…";

    // ✅ Force Safari to flush audio buffer
    recorder.requestData();

    // ✅ Safari needs delay before stop()
    setTimeout(() => {
      recorder.stop();
    }, 500);

    recorder.onstop = async () => {
      try {
        const audioBlob = new Blob(chunks, { type: "audio/mp4" });

        output.textContent =
          `🎧 Audio captured (${Math.round(audioBlob.size / 1024)} KB)`;

        if (audioBlob.size < 3000) {
          output.textContent +=
            "\n❌ Recording failed. Please try again.";
          return;
        }

        output.textContent += "\n⬆ Uploading audio…";

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
          "✅ Transcription complete:\n\n" +
          (data.text || "(No speech detected)");

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
});
