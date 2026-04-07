# 🎙️ Empathy Engine

> **Challenge 1** — Dynamically modulate synthesised speech based on detected emotion.

## What It Does

The Empathy Engine analyses any text input, classifies its emotion into one of **10 granular categories** (happy, excited, sad, frustrated, angry, neutral, inquisitive, surprised, concerned, fearful) with an **intensity score**, then synthesises expressive speech by modulating three vocal parameters:

| Parameter | Mechanism |
|-----------|-----------|
| **Rate** (speed) | `pydub` speed-up / slow-down |
| **Pitch** | Frame-rate resampling (semitone shifting) |
| **Volume** | dB gain adjustment |

The degree of modulation scales linearly with the detected intensity — so *"This is good"* gets a mild pitch lift, while *"THIS IS THE BEST DAY EVER!!!"* gets a pronounced rate increase and significant pitch boost.

## Emotion → Voice Mapping

| Emotion | Rate | Pitch | Volume |
|---------|------|-------|--------|
| happy | +10% | +2 st | +2 dB |
| excited | +25% | +3.5 st | +3.5 dB |
| sad | −18% | −2.5 st | −2 dB |
| frustrated | −10% | −1.5 st | +1.5 dB |
| angry | +15% | −1 st | +4 dB |
| neutral | 0% | 0 st | 0 dB |
| inquisitive | +5% | +1.5 st | +0.5 dB |
| surprised | +20% | +3 st | +2.5 dB |
| concerned | −12% | −1 st | −1 dB |
| fearful | −5% | −0.5 st | −1.5 dB |

Actual applied values are scaled by the detected intensity (0.0–1.0).

## Tech Stack

- **Emotion detection** — Claude API (`claude-opus-4-6`) with structured JSON output
- **TTS synthesis** — gTTS (Google Text-to-Speech)
- **Audio processing** — pydub (rate, pitch, volume)
- **Web interface** — Flask + vanilla JS

## Prerequisites

- Python 3.9+
- **ffmpeg** installed and on `PATH` (required by pydub):
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
  - Windows: download from https://ffmpeg.org/download.html
- An Anthropic API key

## Setup

```bash
# 1. Clone / enter the project directory
cd empathy_engine

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."   # Windows: set ANTHROPIC_API_KEY=sk-ant-...
```

## Running

### Web Interface (recommended)

```bash
python app.py
```

Then open **http://localhost:5000** in your browser. Type any text, click **Detect & Speak**, and the page will:
1. Show the detected emotion, intensity, and reasoning
2. Display the applied vocal parameters
3. Play the modulated audio inline

### CLI (quick test)

```bash
# Test the emotion detector standalone
python emotion_detector.py

# Test the TTS engine standalone
python tts_engine.py
# Outputs: outputs/test_excited.mp3
```

## Project Structure

```
empathy_engine/
├── app.py                  # Flask application
├── emotion_detector.py     # Claude-based emotion classifier
├── tts_engine.py           # gTTS + pydub vocal modulation
├── templates/
│   └── index.html          # Web UI
├── static/
│   └── style.css           # Styling
├── outputs/                # Generated audio files (auto-created)
└── requirements.txt
```

## Design Decisions

1. **Claude for emotion detection** — Rule-based NLP (VADER/TextBlob) only captures positive/negative/neutral. Claude understands nuanced states like "inquisitive" or "concerned" from context, producing more expressive output.

2. **Intensity scaling** — Rather than hard-coded parameter values per emotion, each emotion defines a *target* deviation from neutral. The actual applied parameters are linearly interpolated by intensity, so mild emotions sound subtle and strong emotions sound dramatic.

3. **gTTS + pydub** — gTTS produces natural-sounding English speech (internet connection required). Pydub gives precise control over all three vocal axes without requiring a proprietary TTS API.

4. **Frame-rate pitch shifting** — Pitch is shifted by resampling to a modified frame rate then back to the original, preserving duration while changing tonal height.
