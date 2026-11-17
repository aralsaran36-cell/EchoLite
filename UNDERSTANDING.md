## 1. Project Overview & Problem Statement

**Problem**
Typing is slow, especially on a phone, and many people find it easier to speak. This project builds a browser-based voice assistant that lets users talk naturally in English or Tamil. The user speaks, the system detects when they have finished, and it replies with voice. It uses LiquidAI/LFM3-Omni-2B running on our own server, not on a third-party cloud service. Raw audio is not stored.

**What it is NOT:**
This is strictly a focused, turn-based voice chat interface—not a "Jarvis" system with always-on wake words, background listening, or smart-home controls.

**Who are the intended users?**
People who want to talk by voice directly in their browser, without downloading an app and without pressing stop after every sentence, while also protecting their voice-data privacy.

**Language scope:** 
English must work completely. Tamil and mixed Tamil-English speech are also goals, but the model card does not list Tamil, so their quality is untested.


## 2. System Architecture

flowchart TD
    
flowchart TD
    A["Browser UI: User clicks Start"] --> B{"Mic Permission?"}
    B -->|denied| B1["Show permission error message"]
    B -->|granted| C["Capture Mic Audio + Client VAD"]
    C -->|short pause| C
    C -->|silence threshold met| D["Send audio segment to FastAPI"]
    D --> E["Validate format, size & duration"]
    E -->|invalid audio| E1["Return 400 error to browser"]
    E -->|valid| F["Resample to 16kHz Mono WAV"]
    F --> G["Load Session Text History (32K limit check)"]
    G --> H{"Language / Mode"}
    H -->|English / Primary| I["LFM3-Omni-2B: Audio-to-Audio + Text"]
   H -->|"Tamil fallback - only if approved"| J["Tamil ASR, then LFM3-Omni-2B, then Tamil TTS"]
    I --> K{"Inference OK?"}
    J --> K
    K -->|model/server error| K1["Show error + retry option in UI"]
    K -->|success| L["Save turn text only (Discard raw audio)"]
    L --> M["Return Text + 24kHz Audio + Latency stats"]
    M --> N["Browser: Show Transcript & Play Audio"]
    N -->|user interrupts / clicks stop| O["Abort playback & listen for next turn"]
    N -->|playback ends| C


## 3. End-to-End Data Flow

Browser : The user clicks the Start button to begin the voice conversation.

Microphone Permission : The browser asks for microphone permission.
- Permission denied = Show an error message.
- Permission granted = Start microphone recording.

Audio Capture + VAD : The browser captures microphone audio. VAD (Voice Activity Detection) detects whether the user is speaking or silent.
- User speaking = Continue recording.
- Short pause = Continue recording.
- Silence threshold reached = Complete the audio segment.

Send Audio : The browser sends the completed audio segment to the FastAPI server.

Audio Validation : The server checks the audio format, file size and duration.
- Invalid audio = Return 400 error to the browser.
- Valid audio = Continue processing.

Audio Preprocessing : The server converts the audio into 16 kHz Mono WAV format.

Session History : The server loads the previous conversation text for the current session and checks the 32K token limit.

Language / Mode Selection : The system selects the processing mode.
- English = Primary processing mode.
- Tamil = Fallback mode, only if approved.

AI Model – English : LFM3-Omni-2B processes the incoming audio and generates response text and audio.

AI Model – Tamil Fallback : If approved, the system follows this process:
- Tamil ASR converts speech into text.
- LFM3-Omni-2B generates the response.
- Tamil TTS converts the response text into audio.

Inference Check : The server checks whether AI model processing is successful.
- Success = Continue processing.
- Model/server error = Return an error message and retry option to the browser.

Conversation Storage : Save the conversation text for future context. Raw audio is discarded after processing.

Response Generation : The server prepares and returns:
- Response text.
- Generated audio (24 kHz).
- Processing latency statistics.

Final Response – Browser : The browser displays the response text and plays the generated audio.

User Interruption / Stop : If the user interrupts the AI or clicks Stop, the browser aborts audio playback and prepares to listen for the next input.

Continuous Conversation : If playback finishes, the browser starts listening again. The same process continues until the user stops the conversation.


## 4. Technology Stack

| Technology | Why I chose it |

- Python 3.11+	          - Handles backend logic and audio processing.
- FastAPI + Uvicorn	      - Creates and runs backend APIs.
- Pydantic.    	          - Validates incoming request data.
- HTML, CSS, JS           - Builds the frontend user interface.
- getUserMedia            - Captures microphone audio.
- Silero VAD	          - Detects speech and silence.
- Web Audio API	          - Plays AI-generated audio and stops playback.
- FFmpeg	              - Converts audio into the required format and sample rate.
- LFM3-Omni-2B	          - Understands user speech and generates text and audio replies.
- In-memory session store - Maintains conversation history during a session.
- Python logging          - Records errors and processing time.
- pytest                  - Tests backend functionality.
- HTTPS	                  - Enables microphone access on mobile browsers.


## 5. Risks and Tests

1. Tamil and mixed Tamil-English quality is poor
The model card does not list Tamil. The model may not understand it, may reply in English, or may not speak Tamil.
Test: Run 10 English, 10 Tamil and 10 mixed prompts. Check three things separately: understanding, reply language, spoken audio. Record the results honestly, with examples.

2. VAD cuts the user off or waits too long
A silence threshold that is too short cuts the user in the middle. Too long makes the reply feel slow.
Test: Try 0.8, 1.2 and 2.0 sec on a real phone. Speak with natural pauses and count wrong cut-offs.

3. Noise triggers false speech detection
TV or other people talking can start a turn, or stop VAD from detecting the end.
Test: Record turns in a quiet room, with a fan and with a TV on. Count false starts and missed endings.

4. Browser audio format differs (Chrome WebM, Safari MP4)
The server may fail to decode one of them, or the sample rate may not match the model.
Test: Record on Chrome (desktop), Safari (iPhone) and Chrome (Android). Check that the server accepts all three, and check the converted file’s sample rate with ffprobe.

5. History grows too large
Long conversations may pass the model’s context limit or slow it down.
Test: Run a 30-turn conversation. Check that old turns are removed and the model still replies correctly.

## 6. Milestone Plan with Measurable Completion Criteria

### Milestone 1: Model Feasibility
- Run LFM3-Omni-2B and follow its official model card.
- Test English, Tamil, and Tanglish audio input and output.
- Measure inference latency, RAM/VRAM usage, and confirm audio sample rate and context limit.
- Document language test results and hardware benchmarks.

Done when: English works end to end, and Tamil/Tanglish results and benchmarks are documented.

### Milestone 2: Backend Development
- Build `/health` and `/turn` API endpoints using FastAPI.
- Validate audio format, file size, and duration.
- Convert audio using FFmpeg and integrate the model.
- Add in-memory session history, size limits, and error handling.

Done when: All pytest cases pass and one real English turn works through `/turn`.

### Milestone 3: Browser Voice UI
- Add Start and Stop buttons with microphone permission handling.
- Implement VAD with a configurable silence threshold.
- Add transcript display, text input, and audio playback.
- Build a mobile-friendly UI with HTTPS support.

Done when: Users can speak, hear AI responses, stop, and start new turns on a real phone.

### Milestone 4: Integration and Hardening
- Test 10 consecutive multi-turn conversations.
- Test background noise, long pauses, and network failures.
- Verify privacy: no audio or conversation content in logs or temporary files.
- Prepare README, test results, and demo recording.

Done when: All 10 conversations pass, errors are handled correctly, and privacy checks are clean.

## 7. Three Design Decisions I Made Independently




Decision 1: Use Silero VAD instead of simple energy-based VAD

I chose Silero VAD to detect when the user has finished speaking. I rejected simple energy-based VAD, which detects speech mainly based on audio volume. The reason is that background noise can also have high volume, causing incorrect speech detection. Silero VAD is trained to detect speech, so it is a better starting point for handling real-world audio. The trade-off is that it requires an additional library and may use more resources on mobile devices. Its actual performance must be verified through testing.

Decision 2: Convert audio on the backend using FFmpeg instead of browser-side resampling

I chose backend audio conversion using FFmpeg. The browser sends the recorded audio in its available format, and the backend converts it into the model's required format, such as 16 kHz mono WAV. I rejected browser-side resampling because audio recording and processing behavior can differ between Chrome and Safari. Backend conversion provides one consistent preprocessing path before model inference. The trade-off is that FFmpeg must be installed and maintained on the server.


Decision 3: Use an in-memory session store instead of an SQL database

I chose an in-memory session store to keep conversation history for each session. I rejected an SQL database because this project needs history only during an active session. Memory-only storage also follows the privacy rule, because nothing is written to disk and history is deleted when the session ends. The trade-off is that history is lost if the server restarts and does not continue between sessions.


## 8. Questions for the Task Owner

- 1. Is FFmpeg allowed on the server?

- 2. For mixed Tamil-English speech, which language should the reply use? (ex: Python-la function-na enna, why do we use it?)
