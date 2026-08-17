import os
import uuid
import threading
import re

import yt_dlp
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.ai import generate_video_summary
from app.extractor import get_transcript_for_summary
from app.extractor import (
    get_video_info,
    get_available_subtitles
)

from app.utils import format_duration

from app.downloader import (
    download_video,
    download_audio
)


def get_user_friendly_error(error):
    """
    Convert technical yt-dlp / network errors
    into messages suitable for normal users.
    """



    message = str(error).lower()
    
    if (
    "sign in to confirm" in message
    or "not a bot" in message
    or "confirm you're not a bot" in message
    ):
     return (
        "YouTube is temporarily preventing access "
        "to this video. Please try again in a moment."
    )

    # --------------------------------------
    # Invalid URL
    # --------------------------------------

    if (
        "invalid url" in message
        or "not a valid url" in message
        or "unsupported url" in message
    ):
        return "Please enter a valid YouTube URL."

    # --------------------------------------
    # Video unavailable
    # --------------------------------------

    if (
        "video unavailable" in message
        or "this video is unavailable" in message
        or "not available" in message
    ):
        return "This video is unavailable or does not exist."

    # --------------------------------------
    # Private video
    # --------------------------------------

    if (
        "private video" in message
        or "video is private" in message
    ):
        return "This video is private and cannot be downloaded."

    # --------------------------------------
    # Age restriction
    # --------------------------------------

    if (
        "age-restricted" in message
        or "age restricted" in message
        or "confirm your age" in message
    ):
        return "This video is age restricted and cannot be accessed."

    # --------------------------------------
    # Region restriction
    # --------------------------------------

    if (
        "not available in your country" in message
        or "not available in your region" in message
        or "geo-restricted" in message
    ):
        return "This video is not available in your region."

    # --------------------------------------
    # Login / authentication
    # --------------------------------------

    if (
        "sign in" in message
        or "login required" in message
        or "authentication" in message
    ):
        return "This video requires authentication and cannot be accessed."

    # --------------------------------------
    # Network / DNS
    # --------------------------------------

    if (
        "getaddrinfo failed" in message
        or "network is unreachable" in message
        or "connection reset" in message
        or "connection refused" in message
        or "timed out" in message
        or "timeout" in message
    ):
        return "Couldn't connect to YouTube. Please check your internet connection."

    # --------------------------------------
    # YouTube temporary error
    # --------------------------------------

    if (
        "http error 403" in message
        or "http error 429" in message
        or "too many requests" in message
    ):
        return "YouTube temporarily blocked this request. Please try again in a moment."

    # --------------------------------------
    # Format unavailable
    # --------------------------------------

    if (
        "requested format is not available" in message
        or "format is not available" in message
    ):
        return "The selected quality is not available for this video."

    # --------------------------------------
    # Subtitle errors
    # --------------------------------------

    if (
        "no subtitles" in message
        or "no captions" in message
    ):
        return "No subtitles are available for this video."

    # --------------------------------------
    # Generic download error
    # --------------------------------------

    if (
        "unable to download" in message
        or "downloaderror" in message
        or "download failed" in message
    ):
        return "The download could not be completed. Please try again."

    # --------------------------------------
    # Fallback
    # --------------------------------------

    return "Something went wrong. Please try again."

# ==========================================
# APP
# ==========================================

app = FastAPI(
    title="Downly API",
    description="YouTube audio and video downloader API",
    version="1.0.0"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
             "https://downlycom.onrender.com"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ==========================================
# DOWNLOAD JOBS
# ==========================================

jobs = {}
MAX_ACTIVE_DOWNLOADS = 2

# ==========================================
# AUTOMATIC FILE CLEANUP
# ==========================================

DOWNLOAD_EXPIRY_SECONDS = 30 * 60  # 30 minutes


def cleanup_job_files():
    """
    Delete completed download files
    after they have expired.
    """

    while True:

        try:

            current_time = time.time()

            expired_jobs = []

            for job_id, job in list(jobs.items()):

                # Only clean completed jobs
                if job.get("status") != "completed":
                    continue

                completed_at = job.get(
                    "completed_at"
                )

                if not completed_at:
                    continue

                age = (
                    current_time - completed_at
                )

                if age >= DOWNLOAD_EXPIRY_SECONDS:

                    file_path = job.get(
                        "file_path"
                    )

                    if file_path:

                        try:

                            if os.path.isfile(
                                file_path
                            ):
                                os.remove(
                                    file_path
                                )

                                print(
                                    f"[CLEANUP] "
                                    f"Deleted file: "
                                    f"{file_path}"
                                )

                        except Exception as error:

                            print(
                                f"[CLEANUP ERROR] "
                                f"{error}"
                            )

                    # Delete the entire job folder
                    if file_path:

                        job_folder = os.path.dirname(
                            file_path
                        )

                        try:

                            if (
                                os.path.isdir(
                                    job_folder
                                )
                                and not os.listdir(
                                    job_folder
                                )
                            ):

                                os.rmdir(
                                    job_folder
                                )

                        except Exception as error:

                            print(
                                f"[CLEANUP FOLDER ERROR] "
                                f"{error}"
                            )

                    expired_jobs.append(
                        job_id
                    )

            # Remove expired jobs from memory
            for job_id in expired_jobs:

                jobs.pop(
                    job_id,
                    None
                )

        except Exception as error:

            print(
                f"[CLEANUP ERROR] {error}"
            )

        # Check every 5 minutes
        time.sleep(5 * 60)


# ==========================================
# REQUEST MODELS
# ==========================================

class VideoRequest(BaseModel):

    url: str


class DownloadRequest(BaseModel):

    url: str

    mode: str

    height: int | None = None

    quality: str | None = None


class SubtitleRequest(BaseModel):

    url: str

    language: str = "en"

class SummaryRequest(BaseModel):
    url: str


# ==========================================
# HELPER
# ==========================================

def sanitize_filename(
    filename,
    fallback="subtitle"
):

    if not filename:

        filename = fallback


    # Remove extension temporarily

    filename = os.path.splitext(
        filename
    )[0]


    # Replace invalid Windows characters

    filename = re.sub(
        r'[<>:"/\\|?*\x00-\x1F]',
        "_",
        filename
    )


    # Replace Unicode characters
    # that may cause FileResponse header
    # problems.

    filename = filename.encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    )


    # Clean repeated spaces

    filename = re.sub(
        r"\s+",
        " ",
        filename
    ).strip()


    # Remove trailing dots

    filename = filename.rstrip(".")


    if not filename:

        filename = fallback


    return filename


# ==========================================
# BASIC ENDPOINTS
# ==========================================

@app.get("/")
def root():

    return {
        "message":
            "Downly API is running"
    }


@app.get("/health")
def health():

    return {
        "status":
            "healthy"
    }


@app.get("/debug-youtube")
def debug_youtube(url: str):

    try:

        options = {
            "quiet": False,
            "no_warnings": False,
        }

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        return {
            "success": True,
            "title": info.get("title"),
            "extractor": info.get("extractor"),
            "id": info.get("id"),
        }

    except Exception as error:

        print(
            f"[DEBUG YOUTUBE ERROR] {error}"
        )

        return {
            "success": False,
            "error_type": type(error).__name__,
            "error": str(error),
        }
# ==========================================
# VIDEO INFORMATION
# ==========================================

@app.post("/api/info")
def get_info(
    request: VideoRequest
):

    try:

        info = get_video_info(
            request.url
        )

        formats = []


        for f in info.get(
            "formats",
            []
        ):

            height = f.get(
                "height"
            )

            vcodec = f.get(
                "vcodec"
            )

            acodec = f.get(
                "acodec"
            )


            if (
                height
                and vcodec != "none"
            ):

                formats.append({

                    "format_id":
                        f.get(
                            "format_id"
                        ),

                    "height":
                        height,

                    "fps":
                        f.get(
                            "fps"
                        ),

                    "extension":
                        f.get(
                            "ext"
                        ),

                    "video_codec":
                        vcodec,

                    "audio_codec":
                        acodec,

                    "filesize":
                        (
                            f.get(
                                "filesize"
                            )
                            or
                            f.get(
                                "filesize_approx"
                            )
                        )

                })


        return {

            "title":
                info.get(
                    "title"
                ),

            "uploader":
                info.get(
                    "uploader"
                ),

            "duration":
                info.get(
                    "duration"
                ),

            "duration_formatted":
                format_duration(
                    info.get(
                        "duration"
                    )
                ),

            "thumbnail":
                info.get(
                    "thumbnail"
                ),

            "view_count":
                info.get(
                    "view_count"
                ),

            "formats":
                formats

        }


    except Exception as error:

        print(
            f"[INFO ERROR] {error}"
        )

        raise HTTPException(
            status_code=400,
            detail=get_user_friendly_error(error)
        )


# ==========================================
# START VIDEO / AUDIO DOWNLOAD
# ==========================================

@app.post("/api/download")
def start_download(
    request: DownloadRequest
):

    active_downloads = sum(
        1
        for job in jobs.values()
        if job.get("status") in [
            "starting",
            "downloading"
        ]
    )

    if active_downloads >= MAX_ACTIVE_DOWNLOADS:

        raise HTTPException(
            status_code=429,
            detail=(
                "Downly is currently processing "
                "2 downloads. Please wait for "
                "one to finish and try again."
            )
        )

    # --------------------------------------
    # Validate mode
    # --------------------------------------

    if request.mode not in [
        "video",
        "audio"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Mode must be video or audio"
        )

    # --------------------------------------
    # Validate video quality
    # --------------------------------------

    if (
        request.mode == "video"
        and request.height is None
    ):

        raise HTTPException(
            status_code=400,
            detail="Video height is required"
        )

    # --------------------------------------
    # Validate audio quality
    # --------------------------------------

    if (
        request.mode == "audio"
        and request.quality is None
    ):

        raise HTTPException(
            status_code=400,
            detail="Audio quality is required"
        )

    # --------------------------------------
    # Create job ID
    # --------------------------------------

    job_id = str(
        uuid.uuid4()
    )

    # --------------------------------------
    # Create job
    # --------------------------------------

    jobs[job_id] = {

        "status":
            "starting",

        "progress":
            0,

        "downloaded_bytes":
            0,

        "total_bytes":
            None,

        "speed":
            None,

        "eta":
            None,

        "error":
            None,

        "filename":
            None,

        "file_path":
            None
    }

    # ======================================
    # PROGRESS CALLBACK
    # ======================================

    def update_progress(data):

        if job_id in jobs:

            jobs[job_id].update(
                data
            )


    # ======================================
    # BACKGROUND DOWNLOAD
    # ======================================

    def run_download():

        print(
            f"[{job_id}] "
            f"Download started"
        )


        try:

            # ----------------------------------
            # Ensure downloads directory exists
            # ----------------------------------

            os.makedirs(
                "downloads",
                exist_ok=True
            )


            # ----------------------------------
            # Download
            # ----------------------------------

            if request.mode == "video":

                download_video(

                    request.url,

                    request.height,

                    job_id,

                    update_progress

                )

            else:

                download_audio(

                    request.url,

                    request.quality,

                    job_id,

                    update_progress

                )


            # ----------------------------------
            # Job folder
            # ----------------------------------

            job_folder = os.path.abspath(

                os.path.join(

                    "downloads",

                    job_id

                )

            )


            if not os.path.isdir(
                job_folder
            ):

                raise Exception(
                    "Job download folder was not found."
                )


            # ----------------------------------
            # Find final file
            # ----------------------------------

            files = [

                filename

                for filename
                in os.listdir(
                    job_folder
                )

                if not filename.endswith(
                    (
                        ".part",
                        ".ytdl",
                        ".temp"
                    )
                )

            ]


            if not files:

                raise Exception(

                    "Download completed but "
                    "no output file was found."

                )


            # ----------------------------------
            # Newest file
            # ----------------------------------

            files.sort(

                key=lambda filename:

                    os.path.getmtime(

                        os.path.join(

                            job_folder,

                            filename

                        )

                    ),

                reverse=True

            )


            filename = files[0]


            # ----------------------------------
            # Exact path
            # ----------------------------------

            file_path = os.path.abspath(

                os.path.join(

                    job_folder,

                    filename

                )

            )


            if not os.path.isfile(
                file_path
            ):

                raise Exception(
                    "Output file does not exist."
                )


            # ----------------------------------
            # Completed
            # ----------------------------------

            jobs[job_id].update({
    "status": "completed",
    "progress": 100,
    "filename": filename,
    "file_path": file_path,
    "error": None,

    "completed_at": time.time()
})

            print(
                f"[{job_id}] "
                f"Download completed"
            )

            print(
                f"[{job_id}] "
                f"File: {file_path}"
            )


        except Exception as error:

            # Keep technical error in terminal
            print(
                f"[{job_id}] Technical error: {error}"
            )

            # User-friendly error for frontend
            user_error = get_user_friendly_error(
                error
            )

            jobs[job_id].update({

                "status":
                    "failed",

                "error":
                    user_error

            })

            print(
                f"[{job_id}] "
                f"Download failed: "
                f"{user_error}"
            )


    # ======================================
    # Start thread
    # ======================================

    thread = threading.Thread(

        target=run_download,

        daemon=True

    )


    thread.start()


    return {

        "job_id":
            job_id,

        "status":
            "started"

    }


# ==========================================
# DOWNLOAD STATUS
# ==========================================

@app.get(
    "/api/download/{job_id}/status"
)
def download_status(
    job_id: str
):

    job = jobs.get(
        job_id
    )


    if job is None:

        raise HTTPException(

            status_code=404,

            detail=
                "Download job not found"

        )


    return {

        "job_id":
            job_id,

        **job

    }


# ==========================================
# SEND COMPLETED FILE
# ==========================================

@app.get(
    "/api/download/{job_id}/file"
)
def download_file(
    job_id: str
):

    job = jobs.get(
        job_id
    )


    if job is None:

        raise HTTPException(

            status_code=404,

            detail=
                "Download job not found"

        )


    if job.get(
        "status"
    ) != "completed":

        raise HTTPException(

            status_code=400,

            detail=
                "Download is not completed yet"

        )


    file_path = job.get(
        "file_path"
    )

    filename = job.get(
        "filename"
    )


    if not file_path:

        raise HTTPException(

            status_code=404,

            detail=
                "File path is not available"

        )


    if not os.path.isfile(
        file_path
    ):

        raise HTTPException(

            status_code=404,

            detail=
                "Downloaded file no longer exists"

        )


    # --------------------------------------
    # Determine media type
    # --------------------------------------

    extension = os.path.splitext(

        filename or ""

    )[1].lower()


    if extension == ".mp4":

        media_type = "video/mp4"

    elif extension == ".mp3":

        media_type = "audio/mpeg"

    elif extension == ".webm":

        media_type = "video/webm"

    else:

        media_type = (
            "application/octet-stream"
        )


    # --------------------------------------
    # Safe browser filename
    # --------------------------------------

    safe_name = sanitize_filename(
        filename,
        "download"
    )


    safe_name += extension


    return FileResponse(

        path=file_path,

        filename=safe_name,

        media_type=media_type,

        headers={

            "X-Content-Type-Options":
                "nosniff",

            "Cache-Control":
                "no-store"

        }

    )


# ==========================================
# GET AVAILABLE SUBTITLES
# ==========================================

@app.post(
    "/api/subtitles"
)
def get_subtitles(
    request: SubtitleRequest
):

    try:

        info = get_video_info(
            request.url
        )


        subtitles = get_available_subtitles(
            info
        )


        return {

            "title":
                info.get(
                    "title"
                ),

            "available":
                len(subtitles) > 0,

            "subtitles":
                subtitles

        }


    except Exception as error:

        print(
            f"[SUBTITLE ERROR] {error}"
        )

        raise HTTPException(
            status_code=400,
            detail=get_user_friendly_error(error)
        )


# ==========================================
# DOWNLOAD SUBTITLE
# ==========================================

@app.post(
    "/api/subtitles/download"
)
def download_subtitle(
    request: SubtitleRequest
):

    language = (
        request.language
        or "en"
    ).strip()


    if not language:

        language = "en"


    # --------------------------------------
    # Create subtitle job
    # --------------------------------------

    subtitle_job_id = str(
        uuid.uuid4()
    )


    subtitle_folder = os.path.abspath(

        os.path.join(

            "downloads",

            "subtitles",

            subtitle_job_id

        )

    )


    os.makedirs(
        subtitle_folder,
        exist_ok=True
    )


    try:

        # ----------------------------------
        # Get video information first
        # ----------------------------------

        info = get_video_info(
            request.url
        )


        title = info.get(
            "title"
        ) or "subtitle"


        # ----------------------------------
        # Check available subtitles
        # ----------------------------------

        available = get_available_subtitles(
            info
        )


        available_languages = [

            item["language"]

            for item
            in available

        ]


        # ----------------------------------
        # Match requested language
        # ----------------------------------

        selected_language = None


        # Exact match

        if language in available_languages:

            selected_language = language


        # Try language prefix
        # Example:
        # en -> en-US

        if selected_language is None:

            for item_language in available_languages:

                if (
                    item_language.lower()
                    .startswith(
                        language.lower() + "-"
                    )
                ):

                    selected_language = (
                        item_language
                    )

                    break


        # ----------------------------------
        # No matching language
        # ----------------------------------

        if selected_language is None:

            raise HTTPException(

                status_code=404,

                detail={

                    "message":
                        "Requested subtitle language is not available.",

                    "requested_language":
                        language,

                    "available_languages":
                        available_languages

                }

            )


        # ----------------------------------
        # yt-dlp options
        # ----------------------------------

        output_template = os.path.join(

            subtitle_folder,

            "%(title)s"

        )


        options = {

            "quiet":
                True,

            "no_warnings":
                True,

            "skip_download":
                True,

            "writesubtitles":
                True,

            "writeautomaticsub":
                True,

            "subtitleslangs":
                [selected_language],

            "subtitlesformat":
                "srt/vtt/best",

            "outtmpl":
                output_template

        }


        # ----------------------------------
        # Download subtitle
        # ----------------------------------

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download([
                request.url
            ])


        # ----------------------------------
        # Find subtitle file
        # ----------------------------------

        files = []

        for filename in os.listdir(
            subtitle_folder
        ):

            lower = filename.lower()

            if lower.endswith(
                (
                    ".srt",
                    ".vtt"
                )
            ):

                files.append(
                    filename
                )


        if not files:

            raise Exception(

                "Subtitle extraction completed "
                "but no subtitle file was created."

            )


        # ----------------------------------
        # Prefer SRT
        # ----------------------------------

        srt_files = [

            filename

            for filename
            in files

            if filename.lower().endswith(
                ".srt"
            )

        ]


        if srt_files:

            filename = srt_files[0]

        else:

            filename = files[0]


        file_path = os.path.abspath(

            os.path.join(

                subtitle_folder,

                filename

            )

        )


        if not os.path.isfile(
            file_path
        ):

            raise Exception(
                "Subtitle file does not exist."
            )


        # ----------------------------------
        # Safe filename
        # ----------------------------------

        extension = os.path.splitext(

            filename

        )[1].lower()


        safe_title = sanitize_filename(

            title,

            "subtitle"

        )


        safe_filename = (

            f"{safe_title}"
            f"-{selected_language}"
            f"{extension}"

        )


        # ----------------------------------
        # Media type
        # ----------------------------------

        if extension == ".srt":

            media_type = (
                "application/x-subrip"
            )

        else:

            media_type = (
                "text/vtt"
            )


        # ----------------------------------
        # Return subtitle file
        # ----------------------------------

        return FileResponse(

            path=file_path,

            filename=safe_filename,

            media_type=media_type,

            headers={

                "X-Content-Type-Options":
                    "nosniff",

                "Cache-Control":
                    "no-store"

            }

        )


    except HTTPException:

        raise


    except Exception as error:

        raise HTTPException(

            status_code=400,

            detail=get_user_friendly_error(error)

        )

@app.post("/api/summary")
def generate_summary(
    request: SummaryRequest
):

    try:

        # Get video information
        info = get_video_info(
            request.url
        )

        title = (
            info.get("title")
            or "YouTube Video"
        )

        # --------------------------------
        # Get available captions
        # --------------------------------

        transcript = get_transcript_for_summary(
            info
        )

        if not transcript:

            raise HTTPException(
                status_code=404,
                detail=(
                    "AI Summary is unavailable "
                    "because captions could not "
                    "be accessed for this video."
                )
            )

        # --------------------------------
        # Generate AI summary
        # --------------------------------

        summary = generate_video_summary(
            title,
            transcript
        )

        return {
            "success": True,
            "title": title,
            "summary": summary
        }

    except HTTPException:
        raise

    except Exception as error:

        error_text = str(error).lower()

        print(
            f"[AI SUMMARY ERROR] {error}"
        )

        # YouTube rate limit
        if (
            "429" in error_text
            or "too many requests" in error_text
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "YouTube is temporarily "
                    "limiting caption access. "
                    "Please try the AI Summary "
                    "again after a little while."
                )
            )

        # No captions
        if (
            "subtitle" in error_text
            or "caption" in error_text
        ):

            raise HTTPException(
                status_code=404,
                detail=(
                    "No accessible captions were "
                    "found for this video, so an "
                    "AI Summary cannot be generated."
                )
            )

        raise HTTPException(
            status_code=400,
            detail=get_user_friendly_error(
                error
            )
        )