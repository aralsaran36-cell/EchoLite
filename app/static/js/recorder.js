class AudioRecorder {
  constructor() {
    this.stream = null;
    this.recorder = null;
    this.chunks = [];
    this.startTime = null;
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    this.chunks = [];
    this.recorder = new MediaRecorder(this.stream);

    this.recorder.ondataavailable = event => {
      if (event.data.size > 0) {
        this.chunks.push(event.data);
      }
    };

    this.recorder.start(250);
    this.startTime = Date.now();
  }

  async stop() {
    if (!this.recorder || this.recorder.state === "inactive") {
      return null;
    }

    return new Promise(resolve => {
      this.recorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: "audio/webm" });
        this.cleanup();
        resolve(blob);
      };

      this.recorder.stop();
    });
  }

  getDurationSeconds() {
    if (!this.startTime) return 0;
    return (Date.now() - this.startTime) / 1000;
  }

  cleanup() {
    this.stream?.getTracks().forEach(track => track.stop());
    this.stream = null;
    this.recorder = null;
    this.chunks = [];
    this.startTime = null;
  }
}