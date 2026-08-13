from backend.video_transcription import transcribe_video


video_path = r"G:\Sumit\2019-05-30-164531046.mp4"

result = transcribe_video(video_path)

print("\n===== TRANSCRIPT =====")
print(result["text"])

print("\n===== TIMESTAMP SEGMENTS =====")

for segment in result["segments"]:
    print(
        f"[{segment['start']:.2f}s - {segment['end']:.2f}s] "
        f"{segment['text']}"
    )