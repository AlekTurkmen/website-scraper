# Website Product Scraper

This script scrapes product information and images from specified URLs, saves product data to an Excel file, and processes images by removing their backgrounds.

## Features

- Scrapes product names and prices
- Downloads product images
- Removes backgrounds from images using Replicate API
- Saves product data to Excel file
- Sequential numbering of images

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your Replicate API token:
```
REPLICATE_API_TOKEN=your_token_here
```

## Usage

Run the script:
```bash
python scraper.py
```

The script will:
1. Create necessary folders in a `data` directory
2. Fetch product data from the specified URLs
3. Save product information to `data/products.xlsx`
4. Download original images to `data/original_images/`
5. Save processed images (with backgrounds removed) to `data/processed_images/`

## Output Structure

```
data/
├── products.xlsx
├── original_images/
│   ├── 1.jpg
│   ├── 2.jpg
│   └── ...
└── processed_images/
    ├── 1_no_bg.png
    ├── 2_no_bg.png
    └── ...
``` 