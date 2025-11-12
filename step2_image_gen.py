import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import argparse
import google.generativeai as genai
import certifi

def gemini_generate(api_key, title, description):
    """
    Uses the Gemini API to generate a high-quality, descriptive image prompt.
    """
    print("Generating a creative image prompt with Gemini...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt_template = (
            f"Generate a single, detailed, and vivid image prompt for a news story. The image should be photorealistic and emotionally resonant, suitable for a YouTube video. "
            f"Do not include any text in the image. The prompt should be a descriptive paragraph, not a list of keywords. "
            f"The news story is titled '{title}' and is about: '{description}'. "
            f"Focus on the core theme and create a compelling visual narrative."
        )
        
        response = model.generate_content(prompt_template)
        creative_prompt = response.text.strip().replace("\n", " ")
        print(f"Generated Prompt: {creative_prompt}")
        return creative_prompt
    except Exception as e:
        print(f"Error during Gemini prompt generation: {e}")
        return f"A photorealistic image representing the news story titled '{title}'"

# --- Read News and Generate Prompt ---
def get_image_prompt(news_file, gemini_api_key):
    with open(news_file, 'r', encoding='utf-8') as f:
        news = json.load(f)
    title = news.get('title', '')
    description = news.get('description', '')
    prompt = gemini_generate(gemini_api_key, title, description)
    return prompt

# --- Generate Image via Imagerouter.io ---
def generate_image(prompt, api_key, idx, save_folder):
    # <-- CORRECTED: The URL now includes the required '/openai/' path.
    url = "https://api.imagerouter.io/v1/openai/images/generations"
    
    payload = {
        "prompt": prompt,
        "model": "stabilityai/sdxl-turbo:free",
        "width": 1024,
        "height": 1024,
        "num_outputs": 1
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print(f"Requesting image {idx+1} from ImageRouter...")
    response = requests.post(url, json=payload, headers=headers, verify=certifi.where())
    
    if response.status_code != 200:
        print(f"Error: API request failed for image {idx+1} with status code {response.status_code}.")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    images = data.get('data', [])
    if not images:
        print(f"No images returned in the API response for image {idx+1}. Full response: {data}")
        return None
        
    image_url = images[0].get('url')
    
    if not image_url:
        print(f"No valid image URL found for image {idx+1}")
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
    parser = argparse.ArgumentParser(description="Generates images based on news data using Imagerouter.io and Gemini API.")
    parser.add_argument("--gemini_api_key", required=True, help="Google Gemini API key")
    parser.add_argument("--imagerouter_api_key", required=True, help="Imagerouter.io API key")
    parser.add_argument("--news_file", default="news_output.json", help="Path to the news JSON file (default: news_output.json)")
    args = parser.parse_args()

    prompt = get_image_prompt(args.news_file, args.gemini_api_key)
    
    SAVE_FOLDER = "generated_images"
    NUM_IMAGES = 5

    with ThreadPoolExecutor(max_workers=NUM_IMAGES) as executor:
        futures = [
            executor.submit(generate_image, prompt, args.imagerouter_api_key, i, SAVE_FOLDER)
            for i in range(NUM_IMAGES)
        ]
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"An error occurred in one of the image generation threads: {e}")
            
    print(f"\nImage generation process completed. Check the '{SAVE_FOLDER}' folder.")

if __name__ == "__main__":
    main()