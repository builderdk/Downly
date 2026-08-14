from app.extractor import (
    get_video_info,
    get_available_resolutions
)

from app.downloader import (
    download_video,
    download_audio
)

from app.utils import format_duration


def main():

    print("\n================================")
    print("        DOWNLY DOWNLOADER")
    print("================================")

    url = input("\nEnter YouTube URL: ")

    try:

        info = get_video_info(url)

    except Exception as error:

        print("\nCould not retrieve video.")
        print("Reason:", error)

        return

    print("\n==============================")
    print("VIDEO INFORMATION")
    print("==============================")

    print(
        "Title:",
        info.get("title")
    )

    print(
        "Duration:",
        format_duration(
            info.get("duration")
        )
    )

    print("\nWhat do you want to download?")

    print("1. Video")
    print("2. Audio")

    mode = input("\nChoose option: ")

    if mode == "1":

        resolutions = (
            get_available_resolutions(
                info
            )
        )

        if not resolutions:

            print(
                "No video formats found."
            )

            return

        print(
            "\nAvailable qualities:"
        )

        for i, resolution in enumerate(
            resolutions,
            start=1
        ):

            print(
                f"{i}. {resolution}p"
            )

        choice = input(
            "\nChoose quality: "
        )

        try:

            height = resolutions[
                int(choice) - 1
            ]

        except (
            ValueError,
            IndexError
        ):

            print(
                "Invalid selection."
            )

            return

        print(
            f"\nDownloading {height}p..."
        )

        download_video(
            url,
            height
        )

        print(
            "\nDownload completed!"
        )

    elif mode == "2":

        print(
            "\nAudio quality:"
        )

        print("1. Best")
        print("2. 192 kbps")
        print("3. 128 kbps")

        choice = input(
            "\nChoose quality: "
        )

        quality_map = {
            "1": "0",
            "2": "192",
            "3": "128"
        }

        quality = quality_map.get(
            choice
        )

        if not quality:

            print(
                "Invalid selection."
            )

            return

        print(
            "\nDownloading audio..."
        )

        download_audio(
            url,
            quality
        )

        print(
            "\nDownload completed!"
        )

    else:

        print(
            "Invalid option."
        )


if __name__ == "__main__":
    main()