from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.transcriber import transcribe_video
from services.window_generator import create_windows

from agents.highlight_agent import find_highlights
from agents.refine_agent import refine_highlight

from services.clip_generator import generate_clips

from agents.metadata_agent import generate_metadata

from services.caption_generator import (
    generate_captions_for_all
)

from services.burn_captions import (
    burn_all_captions
)

from services.vertical_converter import (
    convert_all_clips
)

import yt_dlp
import os
import json



from fastapi.staticfiles import StaticFiles

import time


app = FastAPI(title="Orien Studio Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/clips",
    StaticFiles(directory="clips"),
    name="clips"
)


DOWNLOAD_FOLDER = "downloads"

os.makedirs(
    DOWNLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    "outputs",
    exist_ok=True
)


class VideoRequest(BaseModel):
    url: str


@app.get("/")
def home():

    return {
        "message": "Orien Studio Backend Running"
    }


# ==========================
# DOWNLOAD VIDEO
# ==========================

@app.post("/download")
def download_video(data: VideoRequest):


    try:

        download_folder = DOWNLOAD_FOLDER
        for file in os.listdir(
            DOWNLOAD_FOLDER
        ):
            try:
                os.remove(
                    os.path.join(
                        DOWNLOAD_FOLDER,
                        file
                    )
                )
            except:
                pass

        ydl_opts = {

            "format":
            "bestvideo+bestaudio/best",

            "merge_output_format":
            "mp4",

            "outtmpl":
            os.path.join(
                download_folder,
                "%(title)s.%(ext)s"
            ),

            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                data.url,
                download=True
            )

        return {
            
            "status": "success",
            
            "title":
            
            info.get("title"),
            
            "uploader":
            info.get("uploader"),
            
            "duration":
            info.get("duration")
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# ==========================
# TRANSCRIBE VIDEO
# ==========================

@app.post("/transcribe")
def transcribe_latest_video():

    try:

        files = os.listdir(
            DOWNLOAD_FOLDER
        )

        if not files:

            return {
                "error": "No video found"
            }

        latest_file = max(
            [
                os.path.join(
                    DOWNLOAD_FOLDER,
                    f
                )
                for f in files
            ],
            key=os.path.getctime
        )

        result = transcribe_video(
            latest_file
        )

        return {
            "status": "success",
            "video": os.path.basename(
                latest_file
            ),
            "transcript_length": len(
                result["transcript"]
            ),
            "segments": len(
                result["segments"]
            )
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================
# GENERATE HIGHLIGHTS
# ==========================

@app.post("/highlights")
def generate_highlights():

    try:

        segments_file = (
            "outputs/segments.json"
        )

        if not os.path.exists(
            segments_file
        ):
            return {
                "error": "Run /transcribe first"
            }

        with open(
            segments_file,
            "r",
            encoding="utf-8"
        ) as f:

            segments = json.load(f)

        print(
            "Segments Loaded:",
            len(segments)
        )

        windows = create_windows(
            segments
        )

        print(
            "Windows Created:",
            len(windows)
        )

        highlights = find_highlights(
            windows
        )

        with open(
            "outputs/highlights.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                highlights,
                f,
                indent=4
            )

        return {
            "status": "success",
            "windows_created": len(
                windows
            ),
            "highlights": highlights
        }

    except Exception as e:

        print(
            "HIGHLIGHTS ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================
# REFINE HIGHLIGHTS
# ==========================

@app.post("/refine-highlights")
def refine_highlights_endpoint():

    try:

        if not os.path.exists(
            "outputs/highlights.json"
        ):
            return {
                "error":
                "Run /highlights first"
            }

        with open(
            "outputs/segments.json",
            "r",
            encoding="utf-8"
        ) as f:

            segments = json.load(f)

        with open(
            "outputs/highlights.json",
            "r",
            encoding="utf-8"
        ) as f:

            highlights = json.load(f)

        windows = create_windows(
            segments
        )

        refined_clips = []

        for highlight in highlights:

            selected_window = None

            for window in windows:

                if abs(
                    window["start"]
                    -
                    highlight["start"]
                ) < 1:

                    selected_window = window
                    break

            if selected_window:

                refined = refine_highlight(
                    selected_window
                )

                refined_clips.append(
                    refined
                )
                time.sleep(12)

        with open(
            "outputs/refined_clips.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                refined_clips,
                f,
                indent=4
            )

        return {
            "status": "success",
            "clips": refined_clips
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@app.post("/generate-clips")
def create_clips():

    try:

        files = os.listdir(
            DOWNLOAD_FOLDER
        )

        if not files:

            return {
                "error": "No video found"
            }

        latest_video = max(
            [
                os.path.join(
                    DOWNLOAD_FOLDER,
                    f
                )
                for f in files
            ],
            key=os.path.getctime
        )

        generated = generate_clips(
            latest_video
        )

        return {
            "status": "success",
            "clips_created": len(
                generated
            ),
            "clips": generated
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    

@app.post("/generate-metadata")
def metadata():

    with open(
        "outputs/refined_clips.json",
        "r",
        encoding="utf-8"
    ) as f:

        clips = json.load(f)

    results = []

    for clip in clips:

        results.append(
            generate_metadata(
                clip
            )
        )

    with open(
        "outputs/metadata.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=4
        )

    return {
        "status": "success",
        "metadata": results
    }


@app.post("/generate-captions")
def generate_captions():

    try:

        files = (
            generate_captions_for_all()
        )

        return {
            "status": "success",
            "captions_created": len(
                files
            ),
            "files": files
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@app.post("/burn-captions")
def burn_captions():

    try:

        files = burn_all_captions()

        return {
            "status": "success",
            "videos_created": len(
                files
            ),
            "files": files
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    

@app.post("/vertical-shorts")
def vertical_shorts():

    try:

        files = convert_all_clips()

        return {
            "status": "success",
            "videos_created": len(
                files
            ),
            "files": files
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    

@app.get("/results")
def get_results():

    try:

        metadata = []

        if os.path.exists(
            "outputs/metadata.json"
        ):

            with open(
                "outputs/metadata.json",
                "r",
                encoding="utf-8"
            ) as f:

                metadata = json.load(f)

        clips = []

        if os.path.exists(
            "clips"
        ):

            for file in os.listdir(
                "clips"
            ):

                if (
                    file.endswith(
                        "_vertical.mp4"
                    )
                    or
                    file.endswith(
                        "_captioned_vertical.mp4"
                    )
                ):

                    clips.append(file)

        clips.sort()

        return {
            "status": "success",
            "metadata": metadata,
            "clips": clips
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )