import os
import subprocess
from utils.db import get_db

def generate_clips(video_path, project_id):

    clips_folder = os.path.join("clips", project_id)

    os.makedirs(
        clips_folder,
        exist_ok=True
    )

    db = get_db()
    # Query refined clips for this project
    clips_cursor = db.clips.find({"project_id": project_id})
    clips = list(clips_cursor)

    generated_files = []

    for index, clip in enumerate(clips, start=1):
        if (
            "start" not in clip
            or
            "end" not in clip
        ):
            print(f"Skipping invalid clip: {clip}")
            continue
            
        start = clip["start"]
        end = clip["end"]

        output_file = os.path.join(
            clips_folder,
            f"clip_{index}.mp4"
        )

        command = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-ss",
            str(start),
            "-to",
            str(end),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            output_file
        ]

        subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Update clip path and status in database
        db.clips.update_one(
            {"_id": clip["_id"]},
            {
                "$set": {
                    "clip_path": output_file,
                    "status": "generated"
                }
            }
        )

        generated_files.append(
            {
                "file": output_file,
                "start": start,
                "end": end
            }
        )

    return generated_files