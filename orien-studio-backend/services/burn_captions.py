import os
import subprocess
from utils.db import get_db

def burn_caption_on_video(
    video_path,
    srt_path
):

    clips_folder = os.path.dirname(
        os.path.abspath(video_path)
    )

    video_name = os.path.basename(
        video_path
    )

    srt_name = os.path.basename(
        srt_path
    )

    output_name = (
        os.path.splitext(video_name)[0]
        + "_captioned.mp4"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_name,
        "-vf",
        f"subtitles={srt_name}",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_name
    ]

    result = subprocess.run(
        command,
        cwd=clips_folder,
        capture_output=True,
        text=True
    )

    print("\n========== FFMPEG ==========")
    print(result.stderr)
    print("============================\n")

    output_path = os.path.join(
        clips_folder,
        output_name
    )

    if result.returncode != 0:
        print(
            f"Failed: {video_name}"
        )
        return None

    if os.path.exists(
        output_path
    ):
        print(
            f"Created: {output_name}"
        )
        return output_path

    return None


def burn_captions_for_project(project_id):

    db = get_db()
    clips = list(db.clips.find({"project_id": project_id, "clip_path": {"$ne": None}, "srt_path": {"$ne": None}}))

    generated_files = []

    for clip in clips:
        video_path = clip["clip_path"]
        srt_path = clip["srt_path"]

        if os.path.exists(video_path) and os.path.exists(srt_path):
            output_file = burn_caption_on_video(
                video_path,
                srt_path
            )

            if output_file:
                db.clips.update_one(
                    {"_id": clip["_id"]},
                    {
                        "$set": {
                            "captioned_path": output_file
                        }
                    }
                )
                generated_files.append(output_file)

    return generated_files