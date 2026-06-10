from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from services.transcriber import transcribe_video
from services.window_generator import create_windows

from agents.highlight_agent import find_highlights
from agents.refine_agent import refine_highlight

from services.clip_generator import generate_clips
from agents.metadata_agent import generate_metadata

from services.caption_generator import (
    generate_captions_for_project
)

from services.burn_captions import (
    burn_captions_for_project
)

from services.vertical_converter import (
    convert_clips_for_project
)

import yt_dlp
import os
from fastapi.staticfiles import StaticFiles
import time
from datetime import datetime
from utils.db import get_db

app = FastAPI(
    title="Orien Studio Backend",
    description="Backend API for Orien Studio viral clips generator, integrated with MongoDB and ready for Google Cloud Agent Builder tools.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_FOLDER = "downloads"
CLIPS_FOLDER = "clips"

os.makedirs(
    DOWNLOAD_FOLDER,
    exist_ok=True
)
os.makedirs(
    CLIPS_FOLDER,
    exist_ok=True
)

app.mount(
    "/clips",
    StaticFiles(directory=CLIPS_FOLDER),
    name="clips"
)

db = get_db()

class VideoRequest(BaseModel):
    url: str = Field(..., description="The YouTube video URL to download and process.")

class ProjectRequest(BaseModel):
    project_id: Optional[str] = Field(None, description="The unique project ID. If not provided, the latest project will be automatically selected.")

# Helper to resolve active project ID
def get_active_project_id(project_id: Optional[str]) -> str:
    if project_id:
        return project_id
    latest_project = db.projects.find_one(sort=[("created_at", -1)])
    if not latest_project:
        raise HTTPException(status_code=400, detail="No projects found in database. Please call /download first.")
    return latest_project["project_id"]

@app.get("/")
def home():
    return {
        "message": "Orien Studio Backend Running with MongoDB Integration"
    }

# ==========================
# DOWNLOAD VIDEO
# ==========================
@app.post("/download", summary="Download YouTube Video", description="Creates a new project record in MongoDB, downloads the YouTube video, and updates the project details in the database.")
def download_video(data: VideoRequest):
    project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize project document
    db.projects.insert_one({
        "project_id": project_id,
        "url": data.url,
        "status": "created",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    try:
        download_folder = DOWNLOAD_FOLDER
        
        # Clean local download folder to save space
        for file in os.listdir(download_folder):
            try:
                os.remove(os.path.join(download_folder, file))
            except:
                pass

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(download_folder, f"{project_id}_%(title)s.%(ext)s"),
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.url, download=True)
            title = info.get("title")
            uploader = info.get("uploader")
            duration = info.get("duration")
            # Get output path
            filename = ydl.prepare_filename(info)
            video_path = os.path.splitext(filename)[0] + ".mp4"
            if not os.path.exists(video_path):
                # Fallback
                files = os.listdir(download_folder)
                if files:
                    video_path = os.path.join(download_folder, files[0])

        # Update project details
        db.projects.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    "title": title,
                    "uploader": uploader,
                    "duration": duration,
                    "status": "downloaded",
                    "video_path": video_path,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return {
            "status": "success",
            "project_id": project_id,
            "title": title,
            "uploader": uploader,
            "duration": duration
        }

    except Exception as e:
        db.projects.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ==========================
# TRANSCRIBE VIDEO
# ==========================
@app.post("/transcribe", summary="Transcribe Video", description="Transcribes the downloaded video file using Whisper and saves the full transcript and granular segments directly to MongoDB transcripts collection.")
def transcribe_latest_video(data: ProjectRequest):
    try:
        project_id = get_active_project_id(data.project_id)
        project = db.projects.find_one({"project_id": project_id})
        
        if not project or not project.get("video_path") or not os.path.exists(project["video_path"]):
            raise HTTPException(
                status_code=400,
                detail="Downloaded video file not found. Run /download first."
            )

        db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"status": "transcribing", "updated_at": datetime.utcnow()}}
        )

        result = transcribe_video(
            project["video_path"],
            project_id
        )

        db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"status": "transcribed", "updated_at": datetime.utcnow()}}
        )

        return {
            "status": "success",
            "project_id": project_id,
            "video": os.path.basename(project["video_path"]),
            "transcript_length": len(result["transcript"]),
            "segments": len(result["segments"])
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        db.projects.update_one(
            {"project_id": get_active_project_id(data.project_id)},
            {"$set": {"status": "failed", "updated_at": datetime.utcnow()}}
        )
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ==========================
# GENERATE HIGHLIGHTS
# ==========================
@app.post("/highlights", summary="Generate Highlights", description="Queries transcripts from MongoDB, generates candidate engagement windows, and calls Gemini to identify top viral highlights, saving them into the clips collection.")
def generate_highlights(data: ProjectRequest):
    try:
        project_id = get_active_project_id(data.project_id)
        transcript = db.transcripts.find_one({"project_id": project_id})
        
        if not transcript:
            raise HTTPException(
                status_code=400,
                detail="Transcript not found. Run /transcribe first."
            )

        segments = transcript["segments"]
        windows = create_windows(segments)
        highlights = find_highlights(windows)

        # Clear existing clips for this project and insert new ones
        db.clips.delete_many({"project_id": project_id})

        for index, hl in enumerate(highlights, start=1):
            db.clips.insert_one({
                "project_id": project_id,
                "clip_index": index,
                "start": hl["start"],
                "end": hl["end"],
                "hook": hl.get("hook"),
                "reason": hl.get("reason"),
                "score": hl.get("score"),
                "status": "highlighted",
                "created_at": datetime.utcnow()
            })

        db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"status": "highlighted", "updated_at": datetime.utcnow()}}
        )

        return {
            "status": "success",
            "project_id": project_id,
            "windows_created": len(windows),
            "highlights": highlights
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ==========================
# REFINE HIGHLIGHTS
# ==========================
@app.post("/refine-highlights", summary="Refine Engaging Clips", description="Refines start/end boundaries of each candidate highlight to exact sentence timestamps using Gemini, updating the database.")
def refine_highlights_endpoint(data: ProjectRequest):
    try:
        project_id = get_active_project_id(data.project_id)
        transcript = db.transcripts.find_one({"project_id": project_id})
        
        if not transcript:
            raise HTTPException(
                status_code=400,
                detail="Transcript not found. Run /transcribe first."
            )

        clips = list(db.clips.find({"project_id": project_id}))
        if not clips:
            raise HTTPException(
                status_code=400,
                detail="No highlights found. Run /highlights first."
            )

        segments = transcript["segments"]
        windows = create_windows(segments)
        refined_clips = []

        for clip in clips:
            selected_window = None

            for window in windows:
                if abs(window["start"] - clip["start"]) < 1:
                    selected_window = window
                    break

            if selected_window:
                refined = refine_highlight(selected_window)
                
                db.clips.update_one(
                    {"_id": clip["_id"]},
                    {
                        "$set": {
                            "start": refined["start"],
                            "end": refined["end"],
                            "hook": refined.get("hook"),
                            "reason": refined.get("reason"),
                            "score": refined.get("score"),
                            "status": "refined"
                        }
                    }
                )
                refined_clips.append(refined)
                # Rate limit buffer
                time.sleep(12)

        db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"status": "refined", "updated_at": datetime.utcnow()}}
        )

        return {
            "status": "success",
            "project_id": project_id,
            "clips": refined_clips
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
# ==========================
# GENERATE CLIPS (FFMPEG CUTS)
# ==========================
@app.post("/generate-clips", summary="Cut Landscape Clip Videos", description="Performs FFmpeg operations to slice the landscape MP4 clips from the source video using database-refined timestamps.")
def create_clips(data: ProjectRequest):
    try:
        project_id = get_active_project_id(data.project_id)
        project = db.projects.find_one({"project_id": project_id})

        if not project or not project.get("video_path") or not os.path.exists(project["video_path"]):
            raise HTTPException(
                status_code=400,
                detail="Downloaded video file not found. Run /download first."
            )

        generated = generate_clips(
            project["video_path"],
            project_id
        )

        db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"status": "clips_generated", "updated_at": datetime.utcnow()}}
        )

        return {
            "status": "success",
            "project_id": project_id,
            "clips_created": len(generated),
            "clips": generated
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
# ==========================
# GENERATE METADATA
# ==========================
@app.post("/generate-metadata", summary="Generate Viral Metadata", description="Generates short titles, engaging social descriptions, and hashtags using Gemini for all refined clips in the project.")
def metadata(data: ProjectRequest):
    try:
        project_id = get_active_project_id(data.project_id)
        clips = list(db.clips.find({"project_id": project_id}))

        if not clips:
            raise HTTPException(
                status_code=400,
                detail="No clips found in database. Run /highlights first."
            )

        results = []
        for clip in clips:
            meta = generate_metadata(clip)
            db.clips.update_one(
                {"_id": clip["_id"]},
                {
                    "$set": {
                        "title": meta.get("title"),
                        "caption": meta.get("caption"),
                        "hashtags": meta.get("hashtags")
                    }
                }
            )
            results.append(meta)

        return {
            "status": "success",
            "project_id": project_id,
            "metadata": results
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ==========================
# GENERATE CAPTIONS
# ==========================
@app.post("/generate-captions", summary="Generate Subtitles", description="Uses Whisper to transcribe clip audio and generate SRT files for burning captions.")
def generate_captions(data: ProjectRequest):
    try:
        project_id = get_active_project_id(data.project_id)
        files = generate_captions_for_project(project_id)
        return {
            "status": "success",
            "project_id": project_id,
            "captions_created": len(files),
            "files": files
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
# ==========================
# BURN CAPTIONS
# ==========================
@app.post("/burn-captions", summary="Burn Captions onto Video", description="Overlays and burns the SRT subtitles onto landscape clips using FFmpeg.")
def burn_captions(data: ProjectRequest):
    try:
        project_id = get_active_project_id(data.project_id)
        files = burn_captions_for_project(project_id)
        return {
            "status": "success",
            "project_id": project_id,
            "videos_created": len(files),
            "files": files
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
# ==========================
# VERTICAL SHORTS
# ==========================
@app.post("/vertical-shorts", summary="Convert to Vertical Format", description="Scales and crops landscape/captioned clips into vertical 9:16 aspect ratio layout with background blur.")
def vertical_shorts(data: ProjectRequest):
    try:
        project_id = get_active_project_id(data.project_id)
        files = convert_clips_for_project(project_id)
        return {
            "status": "success",
            "project_id": project_id,
            "videos_created": len(files),
            "files": files
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
# ==========================
# GET RESULTS
# ==========================
@app.get("/results", summary="Get Project Results", description="Fetches metadata and final clip details for a project from MongoDB.")
def get_results(project_id: Optional[str] = None):
    try:
        target_project_id = get_active_project_id(project_id)
        
        project = db.projects.find_one({"project_id": target_project_id})
        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        clips_cursor = db.clips.find({"project_id": target_project_id})
        clips = list(clips_cursor)

        # Convert ObjectId to string for JSON serialization
        project["_id"] = str(project["_id"])
        for clip in clips:
            clip["_id"] = str(clip["_id"])

        return {
            "status": "success",
            "project_id": target_project_id,
            "project": project,
            "clips": clips
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )