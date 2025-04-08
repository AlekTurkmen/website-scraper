import yt_dlp
import os

def download_and_convert():
    # URL of the YouTube Short
    url = 'https://www.youtube.com/shorts/SmvaJPzzOE8'
    
    # Define output paths
    output_dir = '/Users/alek/Documents/Parallel/website-scraper/yt-downloader'
    
    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestvideo',  # Select best video-only format
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),  # Output template
        'quiet': False,  # Show progress
        'no_warnings': False,  # Show warnings
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # Convert to MP4
        }],
    }

    # Create a yt-dlp object and download the video
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print("Download and conversion completed successfully!")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    download_and_convert() 