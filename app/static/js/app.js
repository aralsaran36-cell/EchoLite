const chatEl = document.getElementById("chat");
const textInput = document.getElementById("textInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const micArea = document.getElementById("micArea");
const stateLabel = document.getElementById("stateLabel");
const levelFill = document.getElementById("levelFill");
const stopBtn = document.getElementById("stopBtn");
const silenceSelect = document.getElementById("silenceSelect");
const errorBanner = document.getElementById("errorBanner");
const errorText = document.getElementById("errorText");
const retryBtn = document.getElementById("retryBtn");
const audioEl = document.getElementById("assistantAudio");
const tabVoice = document.getElementById("tabVoice");
const tabText = document.getElementById("tabText");
const voicePanel = document.getElementById("voicePanel");
const textPanel = document.getElementById("textPanel");

const API_BASE = "";
const VAD_THRESHOLD = 30;
const MAX_AUDIO_SECONDS = 20;
const NO_SPEECH_MS = 12000;

const USER_ICON = '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8z"/></svg>';
const WAVE_ICON = '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true"><rect x="2" y="9" width="2.5" height="6" rx="1.2"/><rect x="6.5" y="5" width="2.5" height="14" rx="1.2"/><rect x="11" y="2" width="2.5" height="20" rx="1.2"/><rect x="15.5" y="6" width="2.5" height="12" rx="1.2"/><rect x="20" y="9" width="2.5" height="6" rx="1.2"/></svg>';
const SPEAKER_ICON = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5L6 9H3v6h3l5 4z" fill="currentColor"/><path d="M15.5 8.5a5 5 0 010 7"/><path d="M18.5 5.5a9 9 0 010 13"/></svg>';
const CLOCK_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>';

const STATE_LABELS = {
  idle: "Tap mic and speak",
  listening: "Listening...",
  processing: "Thinking...",
  speaking: "Speaking..."
};

const ERROR_MESSAGES = {
  mic: "Microphone permission denied. Allow microphone access and retry.",
  network: "Network disconnected. Check your connection and retry.",
  server: "Model server error. Please try again."
};

let sessionId = crypto.randomUUID();
let recorder = new AudioRecorder();
let player = new AudioPlayer(audioEl);
let vad = null;
let mode = "voice";
let isRecording = false;
let isSending = false;
let playToken = 0;
let levelRaf = null;
let lastFailed = null;

function setState(state, label) {
  micArea.dataset.state = state;
  stateLabel.textContent = label || STATE_LABELS[state];
}

function showError(type, failed) {
  lastFailed = failed;
  errorText.textContent = ERROR_MESSAGES[type];
  errorBanner.classList.remove("hidden");
}

function hideError() {
  lastFailed = null;
  errorBanner.classList.add("hidden");
}

function classifyError(error) {
  if (!navigator.onLine || error instanceof TypeError) return "network";
  return "server";
}

function formatLatency(ms) {
  return `${(ms / 1000).toFixed(1)} s`;
}

function makeAvatar(kind) {
  const el = document.createElement("div");
  el.className = `avatar ${kind}`;
  el.innerHTML = kind === "user" ? USER_ICON : WAVE_ICON;
  return el;
}

function addUserMessage(text) {
  const wrap = document.createElement("div");
  wrap.className = "msg user";

  const col = document.createElement("div");
  col.className = "msg-col";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const label = document.createElement("span");
  label.className = "msg-label";
  label.textContent = "You:";

  const body = document.createElement("span");
  body.className = "msg-text";
  body.textContent = text;

  bubble.append(label, body);
  col.appendChild(bubble);
  wrap.append(col, makeAvatar("user"));
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function addAssistantMessage(text, audioBase64, audioFormat, latencyMs) {
  const wrap = document.createElement("div");
  wrap.className = "msg assistant";

  const col = document.createElement("div");
  col.className = "msg-col";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const label = document.createElement("span");
  label.className = "msg-label";
  label.textContent = "AI:";

  const body = document.createElement("span");
  body.className = "msg-text";
  body.textContent = text;

  bubble.append(label, body);

  if (audioBase64) {
    const replay = document.createElement("button");
    replay.type = "button";
    replay.className = "replay-btn";
    replay.title = "Replay";
    replay.innerHTML = SPEAKER_ICON;
    replay.addEventListener("click", () => {
      playReply(audioBase64, audioFormat, false);
    });
    bubble.appendChild(replay);
  }

  col.appendChild(bubble);

  if (latencyMs != null) {
    const latency = document.createElement("div");
    latency.className = "latency";
    latency.innerHTML = CLOCK_ICON;

    const value = document.createElement("span");
    value.textContent = formatLatency(latencyMs);
    latency.appendChild(value);

    col.appendChild(latency);
  }

  wrap.append(makeAvatar("assistant"), col);
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function disableTextInput(disabled) {
  sendBtn.disabled = disabled;
  textInput.disabled = disabled;
}

function finishIdle() {
  setState("idle");
}

async function playReply(audioBase64, audioFormat, autoListen) {
  if (!audioBase64) {
    if (autoListen && mode === "voice") {
      startVoice();
    } else {
      finishIdle();
    }
    return;
  }

  playToken += 1;
  const token = playToken;

  player.stop();

  if (mode === "voice") setState("speaking");

  await player.playBase64(audioBase64, audioFormat || "wav");

  if (token !== playToken) return;

  if (autoListen && mode === "voice") {
    startVoice();
  } else {
    finishIdle();
  }
}

function stopSpeaking() {
  playToken += 1;
  player.stop();
  finishIdle();
}

async function setMode(newMode) {
  if (newMode === mode) return;

  if (isRecording) {
    await stopVoice(false);
  }

  stopSpeaking();
  hideError();
  mode = newMode;

  const isVoice = mode === "voice";
  tabVoice.classList.toggle("active", isVoice);
  tabText.classList.toggle("active", !isVoice);
  voicePanel.classList.toggle("hidden", !isVoice);
  textPanel.classList.toggle("hidden", isVoice);

  if (!isVoice) textInput.focus();
}

async function requestText(text) {
  isSending = true;
  disableTextInput(true);
  hideError();

  try {
    const response = await fetch(`${API_BASE}/turn/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, text })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    addAssistantMessage(
      data.assistant_text,
      data.audio_base64,
      data.audio_format,
      data.latency_ms
    );

    isSending = false;
    disableTextInput(false);
    textInput.focus();

    playReply(data.audio_base64, data.audio_format, false);
  } catch (error) {
    console.error(error);
    isSending = false;
    disableTextInput(false);
    showError(classifyError(error), { type: "text", text });
  }
}

function sendText() {
  const text = textInput.value.trim();

  if (!text || isSending) return;

  textInput.value = "";
  addUserMessage(text);
  requestText(text);
}

function extensionFor(blob) {
  const type = (blob.type || "").toLowerCase();
  if (type.includes("mp4")) return "mp4";
  if (type.includes("ogg")) return "ogg";
  if (type.includes("wav")) return "wav";
  return "webm";
}

async function sendAudio(blob, duration) {
  if (isSending) return;

  if (duration < 0.5) {
    setState("idle", "Audio too short. Try again.");
    return;
  }

  if (duration > MAX_AUDIO_SECONDS) {
    setState("idle", `Please keep voice under ${MAX_AUDIO_SECONDS} seconds.`);
    return;
  }

  isSending = true;
  hideError();
  setState("processing");

  try {
    const formData = new FormData();
    formData.append("session_id", sessionId);
    formData.append("file", blob, `voice.${extensionFor(blob)}`);

    const response = await fetch(`${API_BASE}/turn`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    addUserMessage(data.user_transcript || "(voice)");
    addAssistantMessage(
      data.assistant_text,
      data.audio_base64,
      data.audio_format,
      data.latency_ms
    );

    isSending = false;
    playReply(data.audio_base64, data.audio_format, true);
  } catch (error) {
    console.error(error);
    isSending = false;
    finishIdle();
    showError(classifyError(error), { type: "voice", blob, duration });
  }
}

function startLevelLoop() {
  const loop = () => {
    if (!isRecording) {
      levelFill.style.width = "0%";
      levelRaf = null;
      return;
    }

    const analyser = vad && vad.analyser;

    if (analyser) {
      const data = new Uint8Array(analyser.frequencyBinCount);
      analyser.getByteFrequencyData(data);

      let sum = 0;
      for (let i = 0; i < data.length; i++) sum += data[i];

      const average = sum / data.length;
      levelFill.style.width = `${Math.min(100, (average / 60) * 100)}%`;
    }

    levelRaf = requestAnimationFrame(loop);
  };

  loop();
}

async function startVoice() {
  if (isRecording || isSending) return;

  hideError();

  try {
    isRecording = true;
    setState("listening");

    await recorder.start();

    vad = new VoiceActivityDetector({
      stream: recorder.stream,
      silenceMs: Number(silenceSelect.value),
      noSpeechMs: NO_SPEECH_MS,
      threshold: VAD_THRESHOLD,
      onSilence: () => {
        stopVoice(true);
      },
      onNoSpeech: async () => {
        await stopVoice(false);
        setState("idle", "No speech heard. Tap mic to try again.");
      }
    });

    await vad.start();
    startLevelLoop();
  } catch (error) {
    console.error(error);
    isRecording = false;
    vad?.stop();
    vad = null;
    await recorder.stop().catch(() => {});
    finishIdle();
    showError("mic", { type: "mic" });
  }
}

async function stopVoice(autoSend = false) {
  if (!isRecording) return;

  isRecording = false;

  vad?.stop();
  vad = null;

  const blob = await recorder.stop();
  const duration = recorder.getDurationSeconds();

  if (!blob || !autoSend) {
    finishIdle();
    return;
  }

  await sendAudio(blob, duration);
}

function retryLast() {
  const failed = lastFailed;
  if (!failed) return;

  hideError();

  if (failed.type === "text") {
    requestText(failed.text);
  } else if (failed.type === "voice") {
    sendAudio(failed.blob, failed.duration);
  } else if (failed.type === "mic") {
    startVoice();
  }
}

tabVoice.addEventListener("click", () => setMode("voice"));
tabText.addEventListener("click", () => setMode("text"));

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

stopBtn.addEventListener("click", stopSpeaking);
retryBtn.addEventListener("click", retryLast);

setState("idle");
