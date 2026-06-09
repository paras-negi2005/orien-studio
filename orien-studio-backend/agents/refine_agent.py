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


def refine_highlight(window):

    prompt = f"""
You are an expert short-form video editor.

You are given a transcript window that has already been identified as highly engaging.

Your job is to find the BEST clip inside this window.

Requirements:

1. Clip length must be between 20 and 40 seconds.
2. Start at the strongest hook possible.
3. End at a complete thought.
4. Do NOT cut off sentences.
5. Do NOT start in the middle of a sentence.
6. Do NOT end in the middle of a sentence.
7. Use ONLY timestamps contained inside the window.
8. Choose the segment with the highest viral potential.

Look for:
- strong hooks
- controversial opinions
- emotional moments
- storytelling
- motivation
- actionable advice
- surprising insights

Return ONLY valid JSON.

Format:

{{
    "start": 518,
    "end": 542,
    "hook": "AI is making students lazy",
    "reason": "Strong controversial statement that creates curiosity",
    "score": 9.8
}}

Window:

{json.dumps(window, ensure_ascii=False)}
"""

    try:

        response = model.generate_content(
            prompt
        )

        text = response.text.strip()

        print("\n========== REFINE RESPONSE ==========")
        print(text)
        print("=====================================\n")

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        ).strip()

        refined_clip = json.loads(text)

        return refined_clip

    except Exception as e:

        print("\n========== REFINE ERROR ==========")
        print(str(e))
        print("==================================\n")

        return {
            "error": str(e),
            "raw_response": text if "text" in locals() else None
        }