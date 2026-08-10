import whisper


# Load Whisper model once when the server starts
model = whisper.load_model("base")


def transcribe_video(video_path: str):

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