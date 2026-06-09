# utils/project_manager.py

import os
from datetime import datetime

def create_project():

    project_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    project_dir = os.path.join(
        "projects",
        project_id
    )

    folders = [
        "downloads",
        "clips",
        "captions",
        "verticals",
        "metadata",
        "transcripts"
    ]

    for folder in folders:
        os.makedirs(
            os.path.join(
                project_dir,
                folder
            ),
            exist_ok=True
        )

    return {
        "project_id": project_id,
        "project_dir": project_dir
    }