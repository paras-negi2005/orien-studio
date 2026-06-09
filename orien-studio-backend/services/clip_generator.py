import os
import json
import subprocess


def generate_clips(video_path):

    clips_folder = "clips"

    os.makedirs(
        clips_folder,
        exist_ok=True
    )

    with open(
        "outputs/refined_clips.json",
        "r",
        encoding="utf-8"
    ) as f:

        clips = json.load(f)

    generated_files = []

    for index, clip in enumerate(clips, start=1):
        if (
            "start" not in clip
            or
            "end" not in clip
        ):
            print(
                f"Skipping invalid clip: {clip}"
                )
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

        generated_files.append(
            {
                "file": output_file,
                "start": start,
                "end": end
            }
        )

    return generated_files