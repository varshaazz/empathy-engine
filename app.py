"""
Empathy Engine — Flask Web Application
Detects emotion from text, modulates TTS vocal parameters, returns audio.
"""

import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_file
from emotion_detector import detect_emotion
from tts_engine import synthesize, EMOTION_VOICE_MAP

app = Flask(__name__)
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html", emotions=list(EMOTION_VOICE_MAP.keys()))


@app.route("/synthesize", methods=["POST"])
def do_synthesize():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Detect emotion
    emotion_data = detect_emotion(text)

    # Generate unique filename
    filename = f"{uuid.uuid4().hex}.mp3"
    output_path = str(OUTPUT_DIR / filename)

    # Synthesise
    result = synthesize(
        text=text,
        emotion=emotion_data["emotion"],
        intensity=emotion_data["intensity"],
        output_path=output_path
    )

    return jsonify({
        "emotion": emotion_data["emotion"],
        "intensity": emotion_data["intensity"],
        "reasoning": emotion_data.get("reasoning", ""),
        "applied_params": result["applied_params"],
        "audio_url": f"/audio/{filename}",
    })


@app.route("/audio/<filename>")
def serve_audio(filename):
    # Sanitise: only allow hex filenames with .mp3 extension
    path = OUTPUT_DIR / filename
    if not path.exists() or path.suffix != ".mp3":
        return jsonify({"error": "Not found"}), 404
    return send_file(str(path), mimetype="audio/mpeg")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
