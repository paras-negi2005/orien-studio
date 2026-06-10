import os
import subprocess
from utils.db import get_db

def convert_to_vertical(video_path):

    output_path = (
        os.path.splitext(video_path)[0]
        + "_vertical.mp4"
    )

    filter_complex = (
        "[0:v]"
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "boxblur=20:10[bg];"

        "[0:v]"
        "scale=1080:-2[fg];"

        "[bg][fg]"
        "overlay=(W-w)/2:(H-h)/2"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i",
        video_path,

        "-filter_complex",
        filter_complex,

        "-c:v",
        "libx264",

        "-preset",
        "fast",

        "-crf",
        "23",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        output_path
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    print("\n========== FFMPEG ==========")
    print(result.stderr)
    print("============================\n")

    if result.returncode != 0:

        print(
            f"Failed: {video_path}"
        )

        return None

    if os.path.exists(
        output_path
    ):

        print(
            f"Created: {output_path}"
        )

        return output_path

    return None


def convert_clips_for_project(project_id):

    db = get_db()
    clips = list(db.clips.find({"project_id": project_id}))

    generated_files = []

    for clip in clips:
        # Prefer captioned_path, fall back to clip_path
        video_path = clip.get("captioned_path") or clip.get("clip_path")

        if video_path and os.path.exists(video_path):
            output_file = convert_to_vertical(video_path)

            if output_file:
                db.clips.update_one(
                    {"_id": clip["_id"]},
                    {
                        "$set": {
                            "vertical_path": output_file,
                            "status": "verticalized"
                        }
                    }
                )
                generated_files.append(output_file)

    return generated_files