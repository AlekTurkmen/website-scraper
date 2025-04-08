# YouTube Short Downloader

This repository contains scripts for downloading and processing YouTube Shorts.

## Requirements

- Python 3.9 or higher
- yt-dlp
- FFmpeg (required for video trimming)

## Installation

1. Install FFmpeg:
   - On macOS: `brew install ffmpeg`
   - On Ubuntu/Debian: `sudo apt install ffmpeg`
   - On Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

2. Install the required Python package:
```bash
pip install -r requirements.txt
```

## Available Scripts

### 1. download_short.py
Downloads the YouTube Short in highest quality without audio:
```bash
python download_short.py
```

### 2. trim_video.py
Downloads the YouTube Short, trims it to start from the 6th second, and saves as MP4 without audio:
```bash
python trim_video.py
```

This script performs a lossless conversion by:
- Downloading the highest quality video stream
- Trimming to start from 6 seconds
- Converting to MP4 without re-encoding the video
- Removing audio
- Maintaining original video quality

The processed video will be saved as 'indacloudLogoVideo.mp4' in the project directory. The script uses a fixed output path to ensure reliable file handling and avoid any filename-related issues. 