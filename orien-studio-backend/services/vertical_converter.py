import os
import subprocess


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


def convert_all_clips():

    clips_folder = "clips"

    generated_files = []

    if not os.path.exists(
        clips_folder
    ):
        return generated_files

    for file in os.listdir(
        clips_folder
    ):

        # Process only captioned videos

        if (
            file.endswith(".mp4")
            and "_vertical" not in file
        ):

            video_path = os.path.join(
                clips_folder,
                file
            )

            output_file = (
                convert_to_vertical(
                    video_path
                )
            )

            if output_file:

                generated_files.append(
                    output_file
                )

    return generated_files