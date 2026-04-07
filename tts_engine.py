"""
TTS Engine — converts text to speech and applies vocal parameter
modulation (rate, pitch, volume) based on detected emotion + intensity.
Uses gTTS for synthesis and pydub for audio post-processing.
"""

import io
import os
from pathlib import Path

from gtts import gTTS
from pydub import AudioSegment
from pydub.effects import speedup

# ---------------------------------------------------------------------------
# Emotion → base vocal parameters
# rate_factor : 1.0 = normal speed  (>1 faster, <1 slower)
# pitch_semitones : 0 = unchanged   (+ higher, - lower)
# volume_db : 0 = unchanged         (+ louder, - softer)
# ---------------------------------------------------------------------------
EMOTION_VOICE_MAP = {
    "happy":      {"rate_factor": 1.10, "pitch_semitones":  2.0, "volume_db":  2.0},
    "excited":    {"rate_factor": 1.25, "pitch_semitones":  3.5, "volume_db":  3.5},
    "sad":        {"rate_factor": 0.82, "pitch_semitones": -2.5, "volume_db": -2.0},
    "frustrated": {"rate_factor": 0.90, "pitch_semitones": -1.5, "volume_db":  1.5},
    "angry":      {"rate_factor": 1.15, "pitch_semitones": -1.0, "volume_db":  4.0},
    "neutral":    {"rate_factor": 1.00, "pitch_semitones":  0.0, "volume_db":  0.0},
    "inquisitive":{"rate_factor": 1.05, "pitch_semitones":  1.5, "volume_db":  0.5},
    "surprised":  {"rate_factor": 1.20, "pitch_semitones":  3.0, "volume_db":  2.5},
    "concerned":  {"rate_factor": 0.88, "pitch_semitones": -1.0, "volume_db": -1.0},
    "fearful":    {"rate_factor": 0.95, "pitch_semitones": -0.5, "volume_db": -1.5},
}


def _interpolate_params(base: dict, intensity: float) -> dict:
    """Scale vocal parameters from neutral by the given intensity."""
    neutral = EMOTION_VOICE_MAP["neutral"]
    return {
        "rate_factor":     neutral["rate_factor"]     + (base["rate_factor"]     - neutral["rate_factor"])     * intensity,
        "pitch_semitones": neutral["pitch_semitones"] + (base["pitch_semitones"] - neutral["pitch_semitones"]) * intensity,
        "volume_db":       neutral["volume_db"]       + (base["volume_db"]       - neutral["volume_db"])       * intensity,
    }


def _shift_pitch(audio: AudioSegment, semitones: float) -> AudioSegment:
    """
    Shift pitch without changing duration by resampling then re-resampling.
    Positive semitones = higher pitch, negative = lower.
    """
    if semitones == 0:
        return audio
    # Each semitone = 2^(1/12) ratio
    ratio = 2 ** (semitones / 12.0)
    original_frame_rate = audio.frame_rate
    # Shift pitch by changing playback rate …
    shifted = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * ratio)
    })
    # … then resample back to the original rate so duration is preserved
    return shifted.set_frame_rate(original_frame_rate)


def synthesize(text: str, emotion: str, intensity: float, output_path: str) -> dict:
    """
    Synthesise text to speech with emotion-driven vocal modulation.

    Args:
        text:        The text to speak.
        emotion:     Detected emotion label (must be in EMOTION_VOICE_MAP).
        intensity:   Emotion intensity 0.0–1.0.
        output_path: Where to save the .mp3 file.

    Returns:
        dict with applied_params and output_path.
    """
    if emotion not in EMOTION_VOICE_MAP:
        emotion = "neutral"

    base_params = EMOTION_VOICE_MAP[emotion]
    params = _interpolate_params(base_params, intensity)

    # ── Step 1: synthesise with gTTS ──────────────────────────────────────
    tts = gTTS(text=text, lang="en", slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    audio = AudioSegment.from_file(buf, format="mp3")

    # ── Step 2: rate (speed) ─────────────────────────────────────────────
    rate = params["rate_factor"]
    if rate != 1.0:
        if rate > 1.0:
            audio = speedup(audio, playback_speed=rate, chunk_size=150, crossfade=25)
        else:
            # Slow down: stretch by changing frame rate then resample
            audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * rate)
            }).set_frame_rate(audio.frame_rate)

    # ── Step 3: pitch ─────────────────────────────────────────────────────
    audio = _shift_pitch(audio, params["pitch_semitones"])

    # ── Step 4: volume ────────────────────────────────────────────────────
    if params["volume_db"] != 0:
        audio = audio + params["volume_db"]

    # ── Step 5: export ───────────────────────────────────────────────────
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    audio.export(output_path, format="mp3")

    return {
        "output_path": output_path,
        "applied_params": {
            "emotion": emotion,
            "intensity": round(intensity, 2),
            "rate_factor": round(params["rate_factor"], 3),
            "pitch_semitones": round(params["pitch_semitones"], 2),
            "volume_db": round(params["volume_db"], 2),
        }
    }


if __name__ == "__main__":
    result = synthesize(
        text="This is absolutely amazing! I can't believe how well it works!",
        emotion="excited",
        intensity=0.9,
        output_path="outputs/test_excited.mp3"
    )
    print(result)
