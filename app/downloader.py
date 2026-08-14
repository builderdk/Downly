import os
import yt_dlp

from app.utils import format_duration, format_size


DOWNLOAD_FOLDER = "downloads"


def progress_hook(
    data,
    progress_callback=None
):

    status = data.get("status")


    # --------------------------------
    # Downloading
    # --------------------------------

    if status == "downloading":

        downloaded = data.get(
            "downloaded_bytes",
            0
        )

        total = (
            data.get("total_bytes")
            or data.get(
                "total_bytes_estimate"
            )
        )

        speed = data.get("speed")

        eta = data.get("eta")


        percentage = 0


        if total:

            percentage = (
                downloaded / total * 100
            )


        progress_data = {

            "status":
                "downloading",

            "progress":
                round(
                    percentage,
                    2
                ),

            "downloaded_bytes":
                downloaded,

            "total_bytes":
                total,

            "speed":
                speed,

            "eta":
                eta,
        }


        # Send progress to API

        if progress_callback:

            progress_callback(
                progress_data
            )


        # Terminal progress

        if total:

            size_text = (

                f"{format_size(downloaded)}"
                f" / "
                f"{format_size(total)}"

            )

        else:

            size_text = format_size(
                downloaded
            )


        speed_text = (

            f"{format_size(speed)}/s"

            if speed

            else
            "Unknown"
        )


        eta_text = (

            format_duration(eta)

            if eta is not None

            else
            "Unknown"
        )


        print(

            f"\rProgress: "
            f"{percentage:6.2f}% | "

            f"{size_text} | "

            f"Speed: "
            f"{speed_text} | "

            f"ETA: "
            f"{eta_text}",

            end="",

            flush=True
        )


    # --------------------------------
    # Download finished
    # --------------------------------

    elif status == "finished":

        print(
            "\nProcessing file..."
        )


        if progress_callback:

            progress_callback({

                "status":
                    "processing",

                "progress":
                    100
            })


# ==================================
# VIDEO DOWNLOAD
# ==================================

def download_video(
    url,
    height,
    job_id,
    progress_callback=None
):

    # Create job-specific folder

    job_folder = os.path.join(
        DOWNLOAD_FOLDER,
        job_id
    )


    os.makedirs(
        job_folder,
        exist_ok=True
    )


    options = {

        # Best video + audio
        # within requested height

        "format": (

            f"bestvideo"
            f"[height<={height}]"
            f"+bestaudio/"
            f"best"
            f"[height<={height}]"
        ),


        # Final output format

        "merge_output_format":
            "mp4",


        # IMPORTANT:
        # Every job has its own folder

        "outtmpl": os.path.join(
            job_folder,
            "%(title)s.%(ext)s"
        ),


        "progress_hooks": [

            lambda data:
            progress_hook(
                data,
                progress_callback
            )
        ],
    }


    print(
        f"[{job_id}] Starting video download..."
    )


    with yt_dlp.YoutubeDL(
        options
    ) as ydl:

        ydl.download([
            url
        ])


# ==================================
# AUDIO DOWNLOAD
# ==================================

def download_audio(
    url,
    quality,
    job_id,
    progress_callback=None
):

    # Create job-specific folder

    job_folder = os.path.join(
        DOWNLOAD_FOLDER,
        job_id
    )


    os.makedirs(
        job_folder,
        exist_ok=True
    )


    options = {

        "format":
            "bestaudio/best",


        # Job-specific output

        "outtmpl": os.path.join(
            job_folder,
            "%(title)s.%(ext)s"
        ),


        # Convert to MP3

        "postprocessors": [

            {

                "key":
                    "FFmpegExtractAudio",

                "preferredcodec":
                    "mp3",

                "preferredquality":
                    quality,
            }

        ],


        "progress_hooks": [

            lambda data:
            progress_hook(
                data,
                progress_callback
            )
        ],
    }


    print(
        f"[{job_id}] Starting audio download..."
    )


    with yt_dlp.YoutubeDL(
        options
    ) as ydl:

        ydl.download([
            url
        ])