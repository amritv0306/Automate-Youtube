import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import argparse

# --- CONFIGURATION ---
# NEWS_JSON = "news_output.json"

SAVE_FOLDER = "generated_images"
NUM_IMAGES = 5

# --- Gemini Prompt Generation (Replace with your Gemini function as needed) ---
def gemini_generate(api_key, title, description):
    # Replace this with your actual Gemini API call if available
    # Here, we simulate a Gemini-generated prompt for demonstration
    prompt = (
        f"Create a vivid, detailed image prompt that visually represents the news titled '{title}'. "
        f"Description: {description}. The image should capture the main theme and feeling of the news."
    )
    return prompt

# --- Read News and Generate Prompt ---
def get_image_prompt(news_file, gemini_api_key):
    with open(news_file, 'r', encoding='utf-8') as f:
        news = json.load(f)
    title = news.get('title', '')
    description = news.get('description', '')
    prompt = gemini_generate(gemini_api_key, title, description)
    # print("Gemini-generated image prompt:")
    # print(prompt)
    return prompt

# --- Generate Image via Imagerouter.io ---
def generate_image(prompt, api_key, idx, save_folder):
    url = "https://api.imagerouter.io/v1/openai/images/generations"
    payload = {
        "prompt": prompt,
        "model": "google/gemini-2.0-flash-exp:free"
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    # Adjust this extraction based on actual API response format
    images = data.get('data', [])
    if not images:
        print(f"No images returned for prompt {idx+1}")
        return None
    image_url = images[0].get('url') if isinstance(images[0], dict) else images[0]
    if not image_url:
        print(f"No valid image URL found for prompt {idx+1}")
        return None
    img_response = requests.get(image_url)
    if img_response.status_code == 200:
        os.makedirs(save_folder, exist_ok=True)
        img_path = os.path.join(save_folder, f"image_{idx+1}.png")
        with open(img_path, 'wb') as img_file:
            img_file.write(img_response.content)
        print(f"Saved image {idx+1} to {img_path}")
        return img_path
    else:
        print(f"Failed to download image {idx+1} from {image_url}")
        return None

# --- Main Execution ---
def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Generates images based on news data using Imagerouter.io and Gemini API.")

    #Add arguments
    parser.add_argument("--gemini_api_key", required=True, help="Google Gemini API key")
    parser.add_argument("--imagerouter_api_key", required=True, help="Imagerouter.io API key")
    NEWS_JSON = "news_output.json"
    parser.add_argument("--news_file", default=NEWS_JSON, help="Path to the news JSON file (default: news_output.json)")

    # Parse arguments
    args = parser.parse_args()

    IMAGEROUTER_API_KEY = args.imagerouter_api_key
    GEMINI_API_KEY = args.gemini_api_key

    if not IMAGEROUTER_API_KEY:
        raise ValueError("IMAGEROUTER_API_KEY environment variable is not set")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    prompt = get_image_prompt(NEWS_JSON, GEMINI_API_KEY)
    with ThreadPoolExecutor(max_workers=NUM_IMAGES) as executor:
        futures = [
            executor.submit(generate_image, prompt, IMAGEROUTER_API_KEY, i, SAVE_FOLDER)
            for i in range(NUM_IMAGES)
        ]
        for future in futures:
            future.result()
    print(f"\nAll images saved in the '{SAVE_FOLDER}' folder.")

if __name__ == "__main__":
    main()
