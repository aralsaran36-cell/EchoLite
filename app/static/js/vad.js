class VoiceActivityDetector {
  constructor({
    stream,
    onSpeechStart,
    onSilence,
    onNoSpeech,
    silenceMs = 1500,
    noSpeechMs = 12000,
    threshold = 30
  }) {
    this.stream = stream;
    this.onSpeechStart = onSpeechStart;
    this.onSilence = onSilence;
    this.onNoSpeech = onNoSpeech;
    this.silenceMs = silenceMs;
    this.noSpeechMs = noSpeechMs;
    this.threshold = threshold;

    this.audioContext = null;
    this.analyser = null;
    this.source = null;
    this.rafId = null;

    this.speaking = false;
    this.heardSpeech = false;
    this.silenceStart = null;
    this.startedAt = null;
    this.stopped = false;
  }

  async start() {
    if (!this.stream) {
      throw new Error("VoiceActivityDetector needs a stream");
    }

    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

    if (this.audioContext.state === "suspended") {
      await this.audioContext.resume();
    }

    this.source = this.audioContext.createMediaStreamSource(this.stream);
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 2048;

    this.source.connect(this.analyser);

    this.stopped = false;
    this.startedAt = Date.now();
    this.loop();
  }

  loop = () => {
    if (this.stopped || !this.analyser) return;

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
        this.heardSpeech = true;
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
    } else if (
      !this.heardSpeech &&
      Date.now() - this.startedAt >= this.noSpeechMs
    ) {
      this.onNoSpeech?.();
      return;
    }

    this.rafId = requestAnimationFrame(this.loop);
  };

  stop() {
    this.stopped = true;

    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }

    this.source?.disconnect();
    this.audioContext?.close();

    this.audioContext = null;
    this.analyser = null;
    this.source = null;
    this.stream = null;
  }
}
