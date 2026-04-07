"""
Emotion Detector — Local (VADER-based, no API required)
"""

from nltk.sentiment import SentimentIntensityAnalyzer

sia = SentimentIntensityAnalyzer()

EMOTION_CATEGORIES = [
    "happy", "excited", "sad", "frustrated", "angry",
    "neutral"
]

def detect_emotion(text: str) -> dict:
    scores = sia.polarity_scores(text)
    compound = scores["compound"]  # range: -1 to +1

    # Emotion classification
    if compound >= 0.6:
        emotion = "excited"
    elif compound >= 0.2:
        emotion = "happy"
    elif compound <= -0.6:
        emotion = "angry"
    elif compound <= -0.2:
        emotion = "frustrated"
    else:
        emotion = "neutral"

    # Intensity scaling (0 to 1)
    intensity = abs(compound)

    
    if "!" in text:
        intensity = min(1.0, intensity + 0.1)
    if text.isupper():
        intensity = min(1.0, intensity + 0.2)

    return {
        "emotion": emotion,
        "intensity": round(intensity, 2),
        "reasoning": f"VADER compound score = {compound}"
    }


if __name__ == "__main__":
    samples = [
        "This is the best day of my life! I got the job!",
        "I am so frustrated with this service. Nothing works.",
        "The meeting is scheduled for 3 PM tomorrow.",
        "WAIT WHAT THIS IS CRAZY!!!",
        "I'm a bit worried about the test results.",
    ]

    for s in samples:
        r = detect_emotion(s)
        print(f"Text : {s}")
        print(f"  → emotion={r['emotion']}, intensity={r['intensity']}")
        print(f"     {r['reasoning']}\n")