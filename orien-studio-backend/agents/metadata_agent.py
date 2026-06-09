import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def generate_metadata(clip):

    prompt = f"""
You are a viral content expert.

Generate:

1. Short title
2. Caption
3. 10 hashtags

Clip:

{json.dumps(clip)}

Return ONLY JSON.

Format:

{{
    "title": "...",
    "caption": "...",
    "hashtags": [
        "#motivation"
    ]
}}
"""

    response = model.generate_content(prompt)

    text = response.text.replace(
        "```json",
        ""
    ).replace(
        "```",
        ""
    ).strip()

    return json.loads(text)