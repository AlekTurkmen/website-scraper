import requests
import pandas as pd
import os
import json
from pathlib import Path
import time
from dotenv import load_dotenv

# Load environment variables (keeping this in case needed for future modifications)
load_dotenv()

def create_folder_structure():
    """Create necessary folders for storing data"""
    # Create main folders
    Path('data').mkdir(parents=True, exist_ok=True)
    Path('data/images').mkdir(exist_ok=True)
    
    return {
        'main': 'data',
        'images': 'data/images'
    }

def fetch_data(urls):
    """Fetch data from multiple URLs and combine the results"""
    all_products = []
    
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and 'items' in data['data']:
                all_products.extend(data['data']['items'])
                
        except requests.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            continue
            
    return all_products

def extract_product_data(products):
    """Extract relevant fields from the products data"""
    extracted_data = []
    
    for idx, product in enumerate(products, 1):
        # Get the lowest price from variants
        if 'variants' in product and product['variants']:
            min_price = min(variant['price'] for variant in product['variants'])
        else:
            min_price = None
            
        # Get the first image URL
        image_url = None
        if 'images' in product and product['images']:
            image_url = product['images'][0]['url']
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
                
        product_data = {
            'id': idx,
            'title': product.get('title', ''),
            'price': min_price,
            'image_url': image_url
        }
        extracted_data.append(product_data)
    
    return extracted_data

def save_to_excel(data, filepath):
    """Save extracted data to Excel file"""
    if not data:
        print("No data to save to Excel")
        return
        
    df = pd.DataFrame(data)
    df['price'] = df['price'].apply(lambda x: f"${x:.2f}" if x else '')
    df = df.drop('image_url', axis=1)  # Remove image_url from Excel output
    df.to_excel(filepath, index=False)

def download_image(url, filepath):
    """Download image from URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"\nError downloading image {url}: {e}")
        return False

def process_images(data, folders):
    """Process all images"""
    if not data:
        print("No data to process")
        return
    
    total_images = len(data)
    successful_downloads = 0
    
    print("Starting image downloads...")
    
    for item in data:
        if item['image_url']:
            # Generate filename using sequential ID
            image_filename = f"{item['id']}.jpg"
            image_path = os.path.join(folders['images'], image_filename)
            
            # Download image
            if download_image(item['image_url'], image_path):
                successful_downloads += 1
                print(f"\rDownloaded ({successful_downloads}/{total_images}) Images", end='', flush=True)
            
            time.sleep(0.1)  # Small delay to prevent overwhelming the server
    
    print("\nImage downloads completed!")
    print(f"Successfully downloaded: {successful_downloads}/{total_images} images")

def main():
    # URLs to scrape
    urls = [
        "https://svc-1000-usf.hotyon.com/search?q=&apiKey=20524fb1-c9b3-44ff-a4ff-ac7a0af066cf&country=US&locale=en&getProductDescription=0&collection=155236663369&skip=0&take=45",
        "https://svc-1000-usf.hotyon.com/search?q=&apiKey=20524fb1-c9b3-44ff-a4ff-ac7a0af066cf&country=US&locale=en&getProductDescription=0&collection=155302461513&skip=0&take=39"
    ]
    
    # Create folder structure
    folders = create_folder_structure()
    
    # Fetch and process data
    print("Fetching product data...")
    raw_data = fetch_data(urls)
    
    print("Extracting product information...")
    products_data = extract_product_data(raw_data)
    
    # Save to Excel
    excel_path = os.path.join(folders['main'], 'products.xlsx')
    print(f"Saving product data to {excel_path}...")
    save_to_excel(products_data, excel_path)
    
    # Process images
    process_images(products_data, folders)

if __name__ == "__main__":
    main() 