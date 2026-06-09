import os
import subprocess


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


def burn_all_captions():

    clips_folder = "clips"

    generated_files = []

    if not os.path.exists(
        clips_folder
    ):
        return generated_files

    for file in os.listdir(
        clips_folder
    ):

        if (
            file.endswith(".mp4")
            and "_captioned"
            not in file
        ):

            video_path = os.path.join(
                clips_folder,
                file
            )

            srt_path = (
                os.path.splitext(
                    video_path
                )[0]
                + ".srt"
            )

            if not os.path.exists(
                srt_path
            ):
                print(
                    f"SRT Missing: {srt_path}"
                )
                continue

            output_file = (
                burn_caption_on_video(
                    video_path,
                    srt_path
                )
            )

            if output_file:
                generated_files.append(
                    output_file
                )

    return generated_files