class AudioPlayer {
  constructor(audioElement) {
    this.audioElement = audioElement;
    this.url = null;
    this.finish = null;
  }

  playBase64(base64, format = "wav") {
    this.stop();

    const bytes = Uint8Array.from(atob(base64), char => char.charCodeAt(0));
    const blob = new Blob([bytes], { type: `audio/${format}` });
    this.url = URL.createObjectURL(blob);

    return new Promise(resolve => {
      const done = () => {
        this.audioElement.onended = null;
        this.audioElement.onerror = null;
        this.finish = null;
        this._revoke();
        resolve();
      };

      this.finish = done;
      this.audioElement.onended = done;
      this.audioElement.onerror = done;
      this.audioElement.src = this.url;

      this.audioElement.play().catch(done);
    });
  }

  stop() {
    this.audioElement.pause();

    if (this.finish) {
      this.finish();
    } else {
      this._revoke();
    }
  }

  _revoke() {
    if (this.url) {
      URL.revokeObjectURL(this.url);
      this.url = null;
    }
  }
}
