import whisper

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("tiny")
    return _model


def transcribe_video(video_path: str):

    model = _get_model()

    result = model.transcribe(
        video_path,
        language="en",
        task="transcribe"
    )

    segments = []

    for segment in result["segments"]:

        segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip()
        })

    return {
        "text": result["text"].strip(),
        "segments": segments
    }
