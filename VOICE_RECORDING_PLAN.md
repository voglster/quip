# Voice Recording Implementation Plan

## Feature Overview
Push-to-talk voice recording with Tab key: Hold Tab → record → release → transcribe text appears.

## Implementation Phases

### Phase 1: Tab Hold Detection (Checkpoint 1)
**Goal**: Prove Tab hold vs tap distinction works reliably

**Tasks**:
- [ ] Implement tab press/release timing logic
- [ ] Add visual feedback for hold detection (simple border color change)
- [ ] Test threshold timing (start with 200ms)
- [ ] Ensure normal tab insertion still works for quick taps
- [ ] Test edge cases (multiple tabs, focus changes, etc.)

**Success Criteria**:
- Quick tab tap (<200ms) inserts `\t` character
- Long tab hold (>200ms) shows visual "recording ready" state
- No false positives/negatives during normal typing

**Files to modify**:
- `desktop/main.py` - Add tab event handlers and timing logic

### Phase 2: Audio Recording & Transcription (Checkpoint 2)
**Goal**: Prove audio capture and whisper transcription works

**Tasks**:
- [ ] Add audio recording with pyaudio or similar
- [ ] Integrate whisper.cpp or whisper Python library
- [ ] Implement basic transcription pipeline
- [ ] Add "Processing..." UI state
- [ ] Test transcription quality and speed
- [ ] Handle transcription errors gracefully

**Success Criteria**:
- Can record 1-10 second audio clips while holding Tab
- Transcription appears as text in the text widget
- Processing time <3 seconds for short clips
- Clear error handling for failed transcription

**Dependencies to add**:
- Audio recording library (pyaudio/sounddevice)
- Whisper transcription (openai-whisper or whisper.cpp Python bindings)

### Phase 3: Audio Feedback & Polish
**Goal**: Add sound effects and refine UX

**Tasks**:
- [ ] Add start/stop recording beeps
- [ ] Implement Ctrl+Z undo for transcribed text
- [ ] Add visual recording indicator (waveform/pulsing dot)
- [ ] Optimize whisper model loading for speed
- [ ] Add configuration options (model size, language, etc.)

**Success Criteria**:
- Satisfying audio feedback on start/stop
- Clean visual states (ready/recording/processing)
- Fast transcription with model pre-loading
- Configurable in TOML settings

## Technical Decisions

### Audio Recording
- **Library**: sounddevice (simpler than pyaudio, cross-platform)
- **Format**: 16kHz WAV (whisper-optimized)
- **Buffer**: Real-time recording while Tab held

### Transcription
- **Engine**: openai-whisper Python library (easier than whisper.cpp bindings)
- **Model**: base or small model for speed/accuracy balance
- **Loading**: Pre-load model on app start, keep in memory

### UI States
1. **Ready**: Normal text widget
2. **Recording**: Red dot + border change + optional waveform
3. **Processing**: Spinner/progress indicator
4. **Error**: Brief red flash + fallback to typing mode

### Audio Feedback
- **Start beep**: Rising tone, ~100ms
- **Stop beep**: Falling tone, ~100ms  
- **Implementation**: pygame mixer or playsound library

## File Structure
```
desktop/
├── main.py                 # Main app (modify for tab handling)
├── voice_recorder.py       # New: audio recording logic
├── transcription.py        # New: whisper integration
├── audio_feedback.py       # New: beep sounds
└── sounds/                 # New: beep audio files
    ├── record_start.wav
    └── record_stop.wav
```

## Configuration Options
Add to `config.toml`:
```toml
[voice]
enabled = true
model_size = "base"           # tiny, base, small, medium, large
language = "auto"             # or "en", "es", etc.
hold_threshold_ms = 200
audio_feedback = true
```

## Testing Strategy
1. **Manual testing**: Various hold durations, background noise, different speech patterns
2. **Edge cases**: Tab while typing, window focus changes, audio device changes
3. **Performance**: Memory usage with whisper loaded, transcription speed
4. **Accessibility**: Works with different keyboard layouts and accessibility tools

## Success Metrics
- **Speed**: Tab hold → text appears in <3 seconds
- **Accuracy**: >90% transcription quality for clear speech
- **Reliability**: No crashes, graceful error handling
- **UX**: Feels natural and responsive, doesn't break typing flow