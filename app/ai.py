import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )
else:
    client = None


def generate_video_summary(
    title,
    transcript
):

    if not client:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    prompt = f"""
You are an expert video summarizer.

Create a concise and useful summary of the
following YouTube video.

Video title:
{title}

Transcript:
{transcript}

Return the result using exactly this structure:

SUMMARY:
Write a clear summary in 2-4 paragraphs.

KEY POINTS:
- Point 1
- Point 2
- Point 3
- Point 4
- Point 5

IMPORTANT:
- Do not invent information.
- Only use information supported by the transcript.
- Keep the language simple and easy to understand.
- If the transcript is incomplete, mention that
  the summary is based on available captions.
"""

    response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents=prompt
)



    return response.text