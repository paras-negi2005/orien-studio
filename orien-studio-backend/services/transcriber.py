import whisper
import os
import json

# Change to "small" later if you want better accuracy
model = whisper.load_model("base")


def transcribe_video(video_path):

    result = model.transcribe(
        video_path,
        fp16=False
    )

    transcript = result["text"]
    segments = result["segments"]

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    with open(
        "outputs/transcript.txt",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(transcript)

    with open(
        "outputs/segments.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            segments,
            f,
            indent=4
        )

    return {
        "transcript": transcript,
        "segments": segments
    }