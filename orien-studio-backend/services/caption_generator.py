import whisper
import os
from utils.db import get_db

model = whisper.load_model("base")


def format_timestamp(seconds):

    hours = int(seconds // 3600)

    minutes = int(
        (seconds % 3600) // 60
    )

    secs = int(seconds % 60)

    milliseconds = int(
        (seconds - int(seconds)) * 1000
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )


def generate_srt(clip_path):

    result = model.transcribe(
        clip_path,
        fp16=False
    )

    segments = result["segments"]

    srt_path = (
        os.path.splitext(
            clip_path
        )[0]
        + ".srt"
    )

    with open(
        srt_path,
        "w",
        encoding="utf-8"
    ) as f:

        for i, segment in enumerate(
            segments,
            start=1
        ):

            start = format_timestamp(
                segment["start"]
            )

            end = format_timestamp(
                segment["end"]
            )

            text = segment[
                "text"
            ].strip()

            f.write(
                f"{i}\n"
            )

            f.write(
                f"{start} --> {end}\n"
            )

            f.write(
                f"{text}\n\n"
            )

    return srt_path


def generate_captions_for_project(project_id):

    db = get_db()
    clips = list(db.clips.find({"project_id": project_id, "clip_path": {"$ne": None}}))

    generated_srt = []

    for clip in clips:
        clip_path = clip["clip_path"]
        if os.path.exists(clip_path):
            srt_file = generate_srt(clip_path)
            db.clips.update_one(
                {"_id": clip["_id"]},
                {
                    "$set": {
                        "srt_path": srt_file,
                        "status": "captioned"
                    }
                }
            )
            generated_srt.append(srt_file)

    return generated_srt