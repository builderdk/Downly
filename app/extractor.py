import yt_dlp
import requests
import re
import os
import glob
import tempfile

# ==========================================
# GET VIDEO INFORMATION
# ==========================================
def get_video_info(url):

    options = {
        "quiet": True,
        "no_warnings": True,
    }

    proxy = os.getenv("YTDLP_PROXY")

    if proxy:
        options["proxy"] = proxy

    with yt_dlp.YoutubeDL(options) as ydl:

        return ydl.extract_info(
            url,
            download=False
        )
# ==========================================
# GET AVAILABLE VIDEO RESOLUTIONS
# ==========================================

def get_available_resolutions(info):

    resolutions = set()

    for f in info.get(
        "formats",
        []
    ):

        height = f.get("height")
        vcodec = f.get("vcodec")

        if (
            height
            and vcodec != "none"
        ):

            resolutions.add(
                height
            )

    return sorted(
        resolutions,
        reverse=True
    )


# ==========================================
# GET AVAILABLE SUBTITLES
# ==========================================

def get_available_subtitles(info):

    subtitles = []

    manual = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}

    language_names = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
        "bn": "Bengali",
        "ta": "Tamil",
        "te": "Telugu",
        "mr": "Marathi",
        "gu": "Gujarati",
        "pa": "Punjabi",
        "ur": "Urdu",
        "kn": "Kannada",
        "ml": "Malayalam",
        "or": "Odia",
        "as": "Assamese",
        "ne": "Nepali",
        "si": "Sinhala",
        "nl": "Dutch",
        "pl": "Polish",
        "tr": "Turkish",
        "vi": "Vietnamese",
        "th": "Thai",
        "id": "Indonesian",
        "sv": "Swedish",
        "da": "Danish",
        "no": "Norwegian",
        "fi": "Finnish",
        "cs": "Czech",
        "uk": "Ukrainian",
        "he": "Hebrew",
        "fa": "Persian",
        "af": "Afrikaans",
        "am": "Amharic",
        "ak": "Akan",
        "ab": "Abkhazian",
        "aa": "Afar",
        "av": "Avaric",
    }

    # -------------------------------
    # Manual subtitles
    # -------------------------------

    for language, tracks in manual.items():

        if not tracks:
            continue

        subtitles.append({
            "language": language,
            "name": language_names.get(
                language.split("-")[0],
                language
            ),
            "automatic": False
        })

    # -------------------------------
    # Automatic captions
    # -------------------------------

    for language, tracks in automatic.items():

        if not tracks:
            continue

        # Don't duplicate manual subtitles
        if any(
            item["language"] == language
            for item in subtitles
        ):
            continue

        subtitles.append({
            "language": language,
            "name": language_names.get(
                language.split("-")[0],
                language
            ),
            "automatic": True
        })

    # -------------------------------
    # Priority
    # -------------------------------

    priority = {
        "en": 0,
        "hi": 1,
        "es": 2,
        "fr": 3,
        "de": 4,
        "pt": 5,
        "ja": 6,
        "ko": 7,
        "zh": 8,
        "ar": 9,
    }

    subtitles.sort(
        key=lambda item: (
            priority.get(
                item["language"].split("-")[0],
                100
            ),
            item["name"].lower()
        )
    )

    return subtitles



def get_transcript_for_summary(info):


    try:

        manual = info.get("subtitles") or {}
        automatic = info.get("automatic_captions") or {}

        # Prefer English, then Hindi
        preferred = [
            "en",
            "en-US",
            "en-GB",
            "hi",
            "hi-IN",
        ]

        selected_tracks = None

        # --------------------------------
        # Manual subtitles
        # --------------------------------

        for language in preferred:

            if language in manual:
                selected_tracks = manual[language]
                break

        # --------------------------------
        # Automatic captions
        # --------------------------------

        if not selected_tracks:

            for language in preferred:

                if language in automatic:
                    selected_tracks = automatic[language]
                    break

        # --------------------------------
        # Fallback to any language
        # --------------------------------

        if not selected_tracks:

            if manual:
                selected_tracks = next(
                    iter(manual.values())
                )

            elif automatic:
                selected_tracks = next(
                    iter(automatic.values())
                )

        if not selected_tracks:
            return None

        # --------------------------------
        # Find VTT track
        # --------------------------------

        selected_track = None

        for track in selected_tracks:

            if track.get("ext") == "vtt":
                selected_track = track
                break

        if not selected_track:
            selected_track = selected_tracks[0]

        subtitle_url = selected_track.get("url")

        if not subtitle_url:
            return None

        # --------------------------------
        # IMPORTANT
        # Use yt-dlp networking
        # --------------------------------

        options = {
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(options) as ydl:

            response = ydl.urlopen(
                subtitle_url
            )

            raw_data = response.read()

        # --------------------------------
        # Convert bytes → string
        # --------------------------------

        if isinstance(raw_data, bytes):

            text = raw_data.decode(
                "utf-8",
                errors="ignore"
            )

        else:

            text = str(raw_data)

        # --------------------------------
        # Remove WEBVTT header
        # --------------------------------

        text = re.sub(
            r"WEBVTT.*?\n",
            "",
            text,
            flags=re.IGNORECASE
        )

        # --------------------------------
        # Remove timestamps
        # --------------------------------

        text = re.sub(
            r"\d{2}:\d{2}(?::\d{2})?\.\d{3}"
            r"\s*-->\s*"
            r"\d{2}:\d{2}(?::\d{2})?\.\d{3}.*",
            "",
            text
        )

        # --------------------------------
        # Remove VTT tags
        # --------------------------------

        text = re.sub(
            r"<[^>]+>",
            "",
            text
        )

        # --------------------------------
        # Clean lines
        # --------------------------------

        lines = []

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.isdigit():
                continue

            lines.append(line)

        # --------------------------------
        # Remove duplicate lines
        # --------------------------------

        cleaned = []

        previous = None

        for line in lines:

            if line == previous:
                continue

            cleaned.append(line)

            previous = line

        transcript = " ".join(
            cleaned
        )

        transcript = transcript[:50000]

        return transcript.strip()

    except Exception as error:

        print(
            f"[TRANSCRIPT ERROR] {error}"
        )

        return None