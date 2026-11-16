const chatEl = document.getElementById("chat");
const textInput = document.getElementById("textInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const voiceStatus = document.getElementById("voiceStatus");
const statusEl = document.getElementById("status");
const audioEl = document.getElementById("assistantAudio");

const API_BASE = "";
const SILENCE_MS = 1500;
const MAX_AUDIO_SECONDS = 20;

let sessionId = crypto.randomUUID();
let recorder = new AudioRecorder();
let vad = null;
let isRecording = false;
let isSending = false;

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setStatus(text) {
  statusEl.textContent = text;
}

function setVoiceStatus(text) {
  voiceStatus.textContent = text;
}

function disableInput(disabled) {
  sendBtn.disabled = disabled;
  textInput.disabled = disabled;
  micBtn.disabled = disabled;
}

async function sendText() {
  const text = textInput.value.trim();

  if (!text || isSending) return;

  textInput.value = "";
  addMessage("user", text);
  await requestTurn({ text });
}

async function sendAudio(blob) {
  if (isSending) return;

  const duration = recorder.getDurationSeconds();

  if (duration < 0.5) {
    setVoiceStatus("Audio too short. Try again.");
    return;
  }

  if (duration > MAX_AUDIO_SECONDS) {
    setVoiceStatus(`Please keep voice under ${MAX_AUDIO_SECONDS} seconds.`);
    return;
  }

  addMessage("user", "🎤 Voice message");
  await requestTurn({ audioBlob: blob });
}

async function requestTurn({ text = "", audioBlob = null }) {
  isSending = true;
  disableInput(true);
  setStatus("Thinking...");

  try {
    const formData = new FormData();
    formData.append("session_id", sessionId);

    if (text) {
      formData.append("text", text);
    }

    if (audioBlob) {
      formData.append("audio", audioBlob, "voice.webm");
    }

    const response = await fetch(`${API_BASE}/turn`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    if (data.user_transcript) {
      addMessage("user", data.user_transcript);
    }

    if (data.assistant_text) {
      addMessage("assistant", data.assistant_text);
    }

    if (data.audio_url) {
      audioEl.src = data.audio_url;
      await audioEl.play().catch(() => {});
    }

    setStatus("Ready");
  } catch (error) {
    console.error(error);
    addMessage("error", "Sorry, I could not process that. Please try again.");
    setStatus("Error");
  } finally {
    isSending = false;
    disableInput(false);
    setVoiceStatus("Tap mic and speak");
  }
}

async function startVoice() {
  if (isRecording || isSending) return;

  try {
    isRecording = true;
    micBtn.classList.add("recording");
    setVoiceStatus("Listening... speak now");
    setStatus("Recording");

    await recorder.start();

    vad = new VoiceActivityDetector({
      silenceMs: SILENCE_MS,
      threshold: 30,
      onSpeechStart: () => {
        setVoiceStatus("Speech detected");
      },
      onSilence: async () => {
        stopVoice(true);
      }
    });

    await vad.start();
  } catch (error) {
    console.error(error);
    isRecording = false;
    micBtn.classList.remove("recording");
    setVoiceStatus("Microphone permission denied");
    setStatus("Ready");
  }
}

async function stopVoice(autoSend = false) {
  if (!isRecording) return;

  isRecording = false;
  micBtn.classList.remove("recording");

  vad?.stop();
  vad = null;

  const blob = await recorder.stop();

  if (!blob) {
    setVoiceStatus("Tap mic and speak");
    setStatus("Ready");
    return;
  }

  if (autoSend) {
    setVoiceStatus("Processing...");
    await sendAudio(blob);
  } else {
    setVoiceStatus("Recording cancelled");
    setStatus("Ready");
  }
}

sendBtn.addEventListener("click", sendText);

textInput.addEventListener("keydown", event => {
  if (event.key === "Enter") {
    event.preventDefault();
    sendText();
  }
});

micBtn.addEventListener("click", () => {
  if (isRecording) {
    stopVoice(false);
  } else {
    startVoice();
  }
});