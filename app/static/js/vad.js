class VoiceActivityDetector {
  constructor({ onSpeechStart, onSilence, silenceMs = 1500, threshold = 30 }) {
    this.onSpeechStart = onSpeechStart;
    this.onSilence = onSilence;
    this.silenceMs = silenceMs;
    this.threshold = threshold;

    this.audioContext = null;
    this.analyser = null;
    this.source = null;
    this.stream = null;
    this.rafId = null;

    this.speaking = false;
    this.silenceStart = null;
    this.stopped = false;
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    this.source = this.audioContext.createMediaStreamSource(this.stream);
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 2048;

    this.source.connect(this.analyser);

    this.stopped = false;
    this.loop();
  }

  loop = () => {
    if (this.stopped) return;

    const data = new Uint8Array(this.analyser.frequencyBinCount);
    this.analyser.getByteFrequencyData(data);

    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      sum += data[i];
    }

    const average = sum / data.length;

    if (average > this.threshold) {
      this.silenceStart = null;

      if (!this.speaking) {
        this.speaking = true;
        this.onSpeechStart?.();
      }
    } else if (this.speaking) {
      if (!this.silenceStart) {
        this.silenceStart = Date.now();
      }

      const silentFor = Date.now() - this.silenceStart;

      if (silentFor >= this.silenceMs) {
        this.speaking = false;
        this.silenceStart = null;
        this.onSilence?.();
        return;
      }
    }

    this.rafId = requestAnimationFrame(this.loop);
  };

  stop() {
    this.stopped = true;

    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }

    this.stream?.getTracks().forEach(track => track.stop());
    this.audioContext?.close();

    this.stream = null;
    this.audioContext = null;
    this.analyser = null;
    this.source = null;
  }
}