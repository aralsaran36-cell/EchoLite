import base64, json, subprocess, time, urllib.request, urllib.error

BASE = "http://localhost:8080"


def post(path, payload):
    req = urllib.request.Request(
        BASE + path,
        json.dumps(payload).encode(),
        {"Content-Type": "application/json"},
    )
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, r.read(), time.time() - t
    except urllib.error.HTTPError as e:
        return e.code, e.read(), time.time() - t


def main():
    subprocess.run(["say", "-o", "/tmp/q.aiff", "What is the capital of France?"], check=True)
    subprocess.run(
        ["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", "/tmp/q.aiff", "/tmp/q.wav"],
        check=True,
    )
    b64 = base64.b64encode(open("/tmp/q.wav", "rb").read()).decode()

    status, body, dt = post("/v1/chat/completions", {
        "messages": [{"role": "user", "content": [
            {"type": "input_audio", "input_audio": {"data": b64, "format": "wav"}}]}],
        "max_tokens": 100,
        "temperature": 0,
    })
    print("CHAT", status, f"{dt:.1f}s")
    print(body[:1500])

    status, body, dt = post("/tts", {"input": "Hello, this is a test."})
    print("TTS", status, f"{dt:.1f}s", len(body), "bytes")
    print(body[:300])


if __name__ == "__main__":
    main()
