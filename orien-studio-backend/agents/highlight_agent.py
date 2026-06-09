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


def find_highlights(windows):

    # Prevent huge prompts
    windows = windows[:100]

    prompt = f"""
You are an expert viral content strategist.

You are given transcript windows extracted from a long video.

Each window contains approximately 30-60 seconds of content.

Your task:

Find the BEST 5 windows for:

- YouTube Shorts
- Instagram Reels
- TikTok

Selection Criteria:

- Strong hook
- Emotional impact
- Storytelling
- Motivation
- Controversial opinions
- Actionable advice
- Surprising insights
- High audience retention potential

IMPORTANT RULES:

1. Use ONLY timestamps provided in the windows.
2. Do NOT invent timestamps.
3. Return ONLY valid JSON.
4. No markdown.
5. No explanations outside JSON.
6. Score should be between 1 and 10.

Return format:

[
    {{
        "start": 120.5,
        "end": 180.2,
        "reason": "Powerful story about success",
        "hook": "The lesson that changed my life",
        "score": 9.8
    }}
]

Windows:

{json.dumps(windows, ensure_ascii=False)}
"""

    try:

        response = model.generate_content(
            prompt
        )

        text = response.text.strip()

        print("\n========== GEMINI HIGHLIGHTS ==========")
        print(text)
        print("=======================================\n")

        # Remove markdown wrappers if Gemini adds them
        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        ).strip()

        highlights = json.loads(text)

        # Sort by score descending
        highlights = sorted(
            highlights,
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        return highlights

    except Exception as e:

        print("\n========== HIGHLIGHT ERROR ==========")
        print(str(e))
        print("=====================================\n")

        return [
            {
                "error": str(e),
                "raw_response": text if "text" in locals() else None
            }
        ]