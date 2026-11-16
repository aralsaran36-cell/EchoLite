class AudioPlayer {
    constructor(audioElement) {
        this.audioElement = audioElement;
    }

    play(blob) {
        const url = URL.createObjectURL(blob);

        this.audioElement.src = url;
        this.audioElement.play();
    }
}