import os
import requests
import json
import replicate
import csv
from dotenv import load_dotenv
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
OUTPUT_DIR = "scraped_data"
OUTPUT_FOLDER = "processed_images"
SCROLL_PAUSE_TIME = 1

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def is_valid_url(url):
    """Validate URL format and accessibility"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_formatted_html(url):
    """Scrape HTML content with dynamic loading"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "web-root"))
        )
        
        scroll_height = 0
        max_attempts = 30
        attempts = 0
        
        while attempts < max_attempts:
            driver.execute_script(f"window.scrollTo({scroll_height}, {scroll_height + 800})")
            scroll_height += 800
            time.sleep(SCROLL_PAUSE_TIME)
            
            images = driver.find_elements(By.CSS_SELECTOR, "img.product-cell__image")
            visible_images = [img for img in images if 
                            driver.execute_script("return arguments[0].getBoundingClientRect().top", img) < 
                            driver.execute_script("return window.innerHeight")]
            
            for img in visible_images:
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: d.execute_script(
                            "return arguments[0].complete && arguments[0].naturalHeight !== 0", img
                        )
                    )
                except:
                    continue
            
            current_height = driver.execute_script("return document.documentElement.scrollHeight")
            if scroll_height >= current_height:
                break
                
            attempts += 1
        
        html_content = driver.page_source
        driver.quit()
        return html_content
        
    except Exception as e:
        print(f"Error scraping HTML: {e}")
        return None

def extract_product_info(html_content):
    """Extract product information from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []
    product_cells = soup.find_all('web-product-cell-r')
    
    for cell in product_cells:
        product = {}
        
        img = cell.find('img', {'class': 'product-cell__image'})
        if img and img.get('src', '').endswith('.jpg'):
            product['image_url'] = img.get('src')
        
        brand = cell.find('span', {'class': 'ss-t-text-ellipsis ss-w-full'})
        if brand:
            product['brand'] = brand.text.strip()
            
        name = cell.find('span', {'data-test': 'product-cell__product-name'})
        if name:
            product['product_name'] = name.text.strip()
            
        price = cell.find('span', {'data-test': 'product-cell__price'})
        if price:
            product['price'] = price.text.strip()
            
        retailer = cell.find('span', {'data-test': 'product-cell__retailer-link'})
        if retailer:
            product['retailer'] = retailer.text.strip()
        
        if product:
            products.append(product)
    
    return products

def save_to_csv(products, category):
    """Save products to CSV file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/{category}_{timestamp}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['brand', 'product_name', 'price', 'retailer', 'image_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for product in products:
            writer.writerow(product)
    
    return filename

def remove_background_with_replicate(image_url, product_name):
    """Remove background from product image"""
    try:
        if not is_valid_url(image_url):
            print(f"✗ Invalid URL for {product_name}")
            return None

        safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_path = os.path.join(OUTPUT_FOLDER, f"{safe_name}.png")

        output = replicate.run(
            "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1",
            input={"image": image_url}
        )

        response = requests.get(output, stream=True)
        response.raise_for_status()
        
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"✓ Processed: {safe_name}")
        return output_path

    except replicate.exceptions.ReplicateError as e:
        print(f"✗ Replicate API Error: {product_name} - {str(e)}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Request Error: {product_name} - {str(e)}")
        return None
    except Exception as e:
        print(f"✗ Unexpected Error: {product_name} - {str(e)}")
        return None

def process_products_backgrounds(products):
    """Process background removal for all products"""
    total = len(products)
    print(f"\nStarting background removal for {total} products...")
    
    for i, product in enumerate(products, 1):
        print(f"\nProcessing {i}/{total}: {product['product_name']}")
        remove_background_with_replicate(
            product['image_url'],
            product['product_name']  # Removed brand prefix
        )

def main():
    if not REPLICATE_API_TOKEN:
        print("Error: REPLICATE_API_TOKEN not found in .env file")
        exit(1)

    print("ShopStyle Scraper and Background Remover")
    print("Takes about 60 seconds to run entirely.")
    print("Enter the ShopStyle URL to scrape (e.g., https://www.shopstyle.com/browse/men/gucci):")
    url = input().strip()
    category = url.split('/')[-1]
    
    # Step 1: Scrape products
    print(f"\nStarting to scrape {url}...")
    html_content = get_formatted_html(url)
    if not html_content:
        print("Failed to get HTML content. Exiting.")
        return
    
    # Step 2: Extract and save product information
    print("\nExtracting product information...")
    products = extract_product_info(html_content)
    csv_file = save_to_csv(products, category)
    print(f"\nFound {len(products)} products")
    print(f"Product data saved to {csv_file}")
    
    # Step 3: Process background removal
    process_products_backgrounds(products)
    print("\nBackground removal process completed!")

if __name__ == "__main__":
    main()