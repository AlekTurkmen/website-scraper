import requests
import csv
import os
import json
from urllib.parse import urljoin
import time
from pathlib import Path
import replicate
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

def create_folder_structure(category_name):
    """Create necessary folders for storing data"""
    # Create main category folder
    Path(category_name).mkdir(parents=True, exist_ok=True)
    
    # Create subfolders for images
    original_images = Path(category_name) / 'original_images'
    processed_images = Path(category_name) / 'processed_images'
    original_images.mkdir(exist_ok=True)
    processed_images.mkdir(exist_ok=True)
    
    return {
        'main': category_name,
        'original': str(original_images),
        'processed': str(processed_images)
    }

def fetch_and_parse_data(url):
    """Fetch data from the URL and parse the JSON response"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def extract_relevant_data(raw_data):
    """Extract relevant fields from the raw data"""
    if not raw_data or 'response' not in raw_data or 'docs' not in raw_data['response']:
        return []
    
    extracted_data = []
    for idx, item in enumerate(raw_data['response']['docs'], 1):
        # Get the lower price from price_range
        price = item.get('price_range', [0])[0] if item.get('price_range') else 0
        
        product_data = {
            'id': idx,  # Add sequential ID
            'title': item.get('title', ''),
            'price': price,  # Only store the lower price
            'thumb_image': item.get('thumb_image', ''),
            'url': item.get('url', '')
        }
        extracted_data.append(product_data)
    
    return extracted_data

def save_to_csv(data, filepath):
    """Save extracted data to CSV file"""
    if not data:
        print("No data to save to CSV")
        return
    
    # Updated fieldnames to match new structure
    fieldnames = ['id', 'title', 'price', 'thumb_image', 'url']
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def download_image(url, filepath):
    """Download image from URL"""
    try:
        response = requests.get(urljoin('https://www.uncommongoods.com', url))
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"\nError downloading image {url}: {e}")
        return False

def remove_background(input_path, output_path):
    """Remove background from image using Replicate API"""
    try:
        # Convert to PNG first
        temp_png_path = input_path.replace('.jpg', '.png')
        with Image.open(input_path) as img:
            # Convert to RGBA to ensure transparency support
            img = img.convert('RGBA')
            img.save(temp_png_path, 'PNG')

        # Use the same model as in scraper.py
        output = replicate.run(
            "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1",
            input={"image": open(temp_png_path, "rb")}
        )

        # Download and save the processed image
        response = requests.get(output, stream=True)
        response.raise_for_status()
        
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        # Clean up temporary PNG file
        if os.path.exists(temp_png_path):
            os.remove(temp_png_path)
            
        return True
    except Exception as e:
        print(f"\nError removing background from {input_path}: {e}")
        # Clean up temporary PNG file in case of error
        if os.path.exists(temp_png_path):
            os.remove(temp_png_path)
        return False

def process_data_and_images(data, folders):
    """Process all data and images"""
    if not data:
        print("No data to process")
        return 0, 0, 0, 0
    
    total_images = len(data)
    successful_downloads = 0
    failed_downloads = 0
    successful_bg_removals = 0
    failed_bg_removals = 0
    
    print("Starting image downloads and processing...")
    
    for item in data:
        if item['thumb_image']:
            # Generate filenames using sequential ID
            jpg_filename = f"{item['id']}.jpg"
            png_filename = f"no_bg_{item['id']}.png"
            original_path = os.path.join(folders['original'], jpg_filename)
            processed_path = os.path.join(folders['processed'], png_filename)
            
            # Download image
            if download_image(item['thumb_image'], original_path):
                successful_downloads += 1
                
                # Remove background
                if remove_background(original_path, processed_path):
                    successful_bg_removals += 1
                else:
                    failed_bg_removals += 1
                
                print(f"\rProcessed ({successful_downloads}/{total_images}) Images - "
                      f"Downloads: {successful_downloads}, "
                      f"Background Removals: {successful_bg_removals}", end='', flush=True)
            else:
                failed_downloads += 1
            
            time.sleep(0.1)
    
    print("\n")
    return successful_downloads, failed_downloads, successful_bg_removals, failed_bg_removals

if __name__ == "__main__":
    if not REPLICATE_API_TOKEN:
        print("Error: REPLICATE_API_TOKEN not found in .env file")
        exit(1)

    # Manual URL for "forhim" category
    url = "https://www.uncommongoods.com/br/search/?account_id=5343&auth_key=&domain_key=uncommongoods&request_type=search&br_origin=searchBox&search_type=category&fl=pid%2Ctitle%2Cthumb_image%2Cthumb_image_alt%2Curl%2Creviews%2Creviews_count%2Cprice_range%2Cbr_min_sale_price%2Cbr_max_sale_price%2Cdays_live%2Cmin_inventory%2Cis_customizable%2Cnum_skus%2Cis_coming_soon%2Cvideo_link%2Cmin_age%2Cmax_age%2Cis_ship_delay%2Cavailability_attr%2Cavailable_inventory%2Cshow_only_on_sale_page%2Cships_within%2Carrives_by_holiday%2Cis_experience%2Cmin_price_sku%2Cmax_price_sku%2Citem_type_id%2Cexperience_dates%2Cavailable_ship_methods%2Csubscription_min_shipments%2Csubscription_min_interval%2Cnew%2Csku_desc1%2Csku_desc2%2Csku_main_image&efq=-show_only_on_sale_page:%221%22&facet.field=ug_cat_internal&facet.field=recipients&facet.field=item_type_id&q=giftsvalentinesdayvalentinesdaygifts&rows=120&start=0&sort=seven_day_sales%20desc&custom_country=US%26custom_country%3D%22US&_br_uid_2=uid=7621295855054:v=16.0:ts=1737049094254:hc=51:cdp_segments=NjYyN2QyYjY4MzYyYmViNTUwMmZjYjRiOjY2MjdkMmI2ODM2MmJlYjU1MDJmY2IxNyw2NjY4OGE5Y2ZlNjEyMzQ0NTYzNDY5MWI6NjY2ODhhOWNmZTYxMjM0NDU2MzQ2OGZk&request_id=2025-1-162100&url=%22%2Fgifts%2Fvalentines-day%2Fvalentines-day-gifts%3Fp%3D1%26s%3Dseven_day_sales%2520desc&ref_url=%22%2Fgifts%2Fvalentines-day%2Fvalentines-day-gifts%22"
    category_name = "valentines-day"  # Manual category name

    try:
        # Create folder structure
        folders = create_folder_structure(category_name)
        
        # Fetch and process data
        raw_data = fetch_and_parse_data(url)
        extracted_data = extract_relevant_data(raw_data)
        
        # Save CSV file
        csv_path = os.path.join(folders['main'], 'uncommongoods_products.csv')
        save_to_csv(extracted_data, csv_path)
        print(f"Data saved to {csv_path}")
        
        # Download images and process backgrounds
        successful_dl, failed_dl, successful_bg, failed_bg = process_data_and_images(extracted_data, folders)
        print(f"\nDownload Summary for {category_name}:")
        print(f"Successfully downloaded: {successful_dl} images")
        print(f"Failed downloads: {failed_dl} images")
        print(f"Successfully removed backgrounds: {successful_bg} images")
        print(f"Failed background removals: {failed_bg} images")
        
    except Exception as e:
        print(f"An error occurred processing {category_name}: {e}")