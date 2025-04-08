import yt_dlp

def download_short():
    # URL of the YouTube Short
    url = 'https://www.youtube.com/shorts/SmvaJPzzOE8'

    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestvideo',  # Select best video-only format
        'outtmpl': '%(title)s.%(ext)s',  # Output template
        'quiet': False,  # Show progress
        'no_warnings': False,  # Show warnings
    }

    # Create a yt-dlp object and download the video
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print("Download completed successfully!")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    download_short() 