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

def load_categories():
    """Load and display available categories"""
    with open('sitemap.json', 'r') as f:
        categories = json.load(f)
    return [cat['label'] for cat in categories]

def prompt_category_selection(categories):
    """Prompt user to select a category"""
    print("\nAvailable categories:")
    for idx, category in enumerate(categories, 1):
        print(f"{idx}. {category}")
    
    while True:
        try:
            choice = int(input("\nEnter the number of the category you want to scrape: "))
            if 1 <= choice <= len(categories):
                return categories[choice - 1]
            print(f"Please enter a number between 1 and {len(categories)}")
        except ValueError:
            print("Please enter a valid number")

def generate_url(category):
    """Generate URL for the selected category"""
    base_url = "https://www.uncommongoods.com/br/search/?"
    url = "https://www.uncommongoods.com/br/search/?account_id=5343&auth_key=&domain_key=uncommongoods&request_type=search&br_origin=searchBox&search_type=category&fl=pid%2Ctitle%2Cthumb_image%2Cthumb_image_alt%2Curl%2Creviews%2Creviews_count%2Cprice_range%2Cbr_min_sale_price%2Cbr_max_sale_price%2Cdays_live%2Cmin_inventory%2Cis_customizable%2Cnum_skus%2Cis_coming_soon%2Cvideo_link%2Cmin_age%2Cmax_age%2Cis_ship_delay%2Cavailability_attr%2Cavailable_inventory%2Cshow_only_on_sale_page%2Cships_within%2Carrives_by_holiday%2Cis_experience%2Cmin_price_sku%2Cmax_price_sku%2Citem_type_id%2Cexperience_dates%2Cavailable_ship_methods%2Csubscription_min_shipments%2Csubscription_min_interval%2Cnew%2Csku_desc1%2Csku_desc2%2Csku_main_image&efq=-show_only_on_sale_page:%221%22&facet.field=ug_cat_internal&facet.field=recipients&facet.field=item_type_id"
    
    # Replace the category in the URL
    url = url + f"&q={category}&rows=120&start=240&sort=seven_day_sales%20desc&custom_country=US%26custom_country%3D%22US&_br_uid_2=uid=7621295855054:v=16.0:ts=1737049094254:hc=20&request_id=2025-1-161400&url=%22%2F{category}%3Fp%3D3%26s%3Dseven_day_sales%2520desc&ref_url=%22%2F{category}%22"
    
    return url

def fetch_and_parse_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data. HTTP Status Code: {response.status_code}")

def extract_relevant_data(data):
    items = data.get("response", {}).get("docs", [])
    extracted_data = []

    for idx, item in enumerate(items, 1):  # Start enumeration at 1
        extracted_data.append({
            "id": idx,
            "title": item.get("title"),
            "price_min": item.get("price_range", [None, None])[0],
            "thumb_image": item.get("thumb_image"),
            "url": item.get("url")
        })
    return extracted_data

def create_folder_structure(base_folder):
    """Create the necessary folder structure"""
    folders = {
        'main': base_folder,
        'images': os.path.join(base_folder, 'thumb_images'),
        'processed': os.path.join(base_folder, 'processed_images')  # New folder for processed images
    }
    
    for folder in folders.values():
        os.makedirs(folder, exist_ok=True)
    
    return folders

def save_to_csv(data, filepath):
    """Save data to CSV file"""
    with open(filepath, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "title", "price_min", "thumb_image", "url"])
        writer.writeheader()
        writer.writerows(data)

def download_image(image_url, save_path, base_url="https://www.uncommongoods.com"):
    """Download an image from URL and save it to specified path"""
    try:
        full_url = urljoin(base_url, image_url)
        response = requests.get(full_url)
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        return False
    except Exception as e:
        print(f"Error downloading image {image_url}: {e}")
        return False

def convert_to_png(jpg_path, png_path):
    """Convert JPG image to PNG format"""
    try:
        with Image.open(jpg_path) as img:
            # Convert to RGBA to ensure transparency support
            img = img.convert('RGBA')
            img.save(png_path, 'PNG')
        return True
    except Exception as e:
        print(f"\nError converting image to PNG: {e}")
        return False

def remove_background(image_path, output_path):
    """Remove background from product image using Replicate API"""
    try:
        # Convert jpg to png first
        temp_png_path = image_path.replace('.jpg', '.png')
        if not convert_to_png(image_path, temp_png_path):
            return False

        # Use the PNG file for background removal
        output = replicate.run(
            "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1",
            input={"image": open(temp_png_path, "rb")}
        )

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
        print(f"\nError removing background: {e}")
        # Clean up temporary PNG file in case of error
        if os.path.exists(temp_png_path):
            os.remove(temp_png_path)
        return False

def get_filename_from_id(item_id, extension='.jpg'):
    """Generate filename from ID with specified extension"""
    return f"{item_id}{extension}"

def process_data_and_images(data, folders):
    """Process the data and download images"""
    successful_downloads = 0
    successful_bg_removals = 0
    failed_downloads = 0
    failed_bg_removals = 0
    total_images = len(data)
    
    print("Starting image downloads and processing...")
    
    for item in data:
        if item['thumb_image']:
            jpg_filename = get_filename_from_id(item['id'], '.jpg')
            png_filename = get_filename_from_id(item['id'], '.png')
            image_path = os.path.join(folders['images'], jpg_filename)
            processed_path = os.path.join(folders['processed'], f"no_bg_{png_filename}")
            
            # Download image
            if download_image(item['thumb_image'], image_path):
                successful_downloads += 1
                
                # Remove background
                if remove_background(image_path, processed_path):
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

    # Load and display categories
    categories = load_categories()
    selected_category = prompt_category_selection(categories)
    
    print(f"\nSelected category: {selected_category}")
    url = generate_url(selected_category)

    try:
        # Create folder structure
        folders = create_folder_structure(selected_category)
        
        # Fetch and process data
        raw_data = fetch_and_parse_data(url)
        extracted_data = extract_relevant_data(raw_data)
        
        # Save CSV file
        csv_path = os.path.join(folders['main'], 'uncommongoods_products.csv')
        save_to_csv(extracted_data, csv_path)
        print(f"Data saved to {csv_path}")
        
        # Download images and process backgrounds
        successful_dl, failed_dl, successful_bg, failed_bg = process_data_and_images(extracted_data, folders)
        print(f"\nDownload Summary for {selected_category}:")
        print(f"Successfully downloaded: {successful_dl} images")
        print(f"Failed downloads: {failed_dl} images")
        print(f"Successfully removed backgrounds: {successful_bg} images")
        print(f"Failed background removals: {failed_bg} images")
        
    except Exception as e:
        print(f"An error occurred processing {selected_category}: {e}")
