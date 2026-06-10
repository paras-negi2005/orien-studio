import whisper
import os
from datetime import datetime
from utils.db import get_db

# Change to "small" later if you want better accuracy
model = whisper.load_model("base")


def transcribe_video(video_path, project_id):

    result = model.transcribe(
        video_path,
        fp16=False
    )

    transcript = result["text"]
    segments = result["segments"]

    # Save to MongoDB
    db = get_db()
    db.transcripts.update_one(
        {"project_id": project_id},
        {
            "$set": {
                "transcript_text": transcript,
                "segments": segments,
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )

    return {
        "transcript": transcript,
        "segments": segments
    }
