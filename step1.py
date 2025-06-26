# To get the latest and trending news (its tittle, its description and the tags)

from google import genai
from google.genai.types import GenerateContentConfig
# import os
import datetime
import argparse
import json
import time

def get_formatted_date():
    today = datetime.date.today()
    day = today.day

    # Add suffix to day
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    day_with_suffix = f"{day}{suffix}"
    return f"{day_with_suffix} {today.strftime('%B')}, {today.year}"

def safe_generate_content(client, model, prompt, max_retries=5):
    system_instruction = "You are an AI news aggregator. Utilize your access to real-time internet data to determine what news stories are currently receiving the most attention, engagement, and discussion across various platforms (news websites, social media, forums, etc.). Prioritize topics that are rapidly gaining traction."
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model, 
                contents=prompt,
                config =  GenerateContentConfig(
                    system_instruction=system_instruction,
                ),
            )
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"Gemini API unavailable (attempt {attempt+1}/{max_retries}). Retrying in 3 seconds...")
                time.sleep(3)
            else:
                raise
    raise RuntimeError("Gemini API unavailable after multiple retries.")

def generate_trending_news_content(api_key):
    """Generate information about the latest trending news using Google Gemini."""
    # Configure the Gemini API client
    client = genai.Client(api_key=api_key)
    
    # Current date context to help the model generate timely content
    current_date = get_formatted_date()
    
    # Generate a title for the trending news
    title_prompt = f"Generate a catchy title for the latest trending news over internet on {current_date} in India. Don't include any punctuation, quotes. Keep it under 100 characters. Don't give option, pick anyone according to you."
    # title_prompt = f"Generate the latest news about air india crash in ahemdabad, india. Just give me the title, no statement. Don't include any punctuation, quotes."
    # title_response = client.models.generate_content(
    #     model="gemini-2.0-flash",
    #     contents=title_prompt
    # )
    title_response = safe_generate_content(
        client, 
        "gemini-2.0-flash", 
        title_prompt
    )
    # Extract and process the generated content
    title = sanitize_metadata(title_response.text)
    
    # Generate a description for the trending news
    desc_prompt = f"Write a 100 words description summarizing the latest trending news on {title}. Just give me the description, no tittle. Dont include \" quotes. "
    # desc_response = client.models.generate_content(
    #     model="gemini-2.0-flash",
    #     contents=desc_prompt
    # )
    desc_response = safe_generate_content(
        client, 
        "gemini-2.0-flash", 
        desc_prompt
    )
    
    # Generate tags for the trending news
    tags_prompt = f"Generate 10 relevant tags related to {title}, comma separated. Just give me the tags, no statement. Inlcude hashtags with each tags."
    # tags_response = client.models.generate_content(
    #     model="gemini-2.0-flash",
    #     contents=tags_prompt
    # )
    tags_response = safe_generate_content(
        client, 
        "gemini-2.0-flash", 
        tags_prompt
    )

    # Extract and process the generated content
    description = desc_response.text.strip()
    tags = [tag.strip() for tag in tags_response.text.split(',')]
    
    return {
        "title": title,
        "description": description,
        "tags": tags
    }

def sanitize_metadata(text):
    """Sanitize text to remove problematic characters."""
    # Remove angle brackets which are explicitly not allowed
    sanitized = text.replace('<', '').replace('>', '')
    # Remove other potentially problematic characters
    # Trim whitespace
    sanitized = sanitized.strip()
    return sanitized

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Generate trending news information using Google Gemini API")
    
    # Add arguments
    parser.add_argument("--api-key", "-k", required=True, help="Google Gemini API key")
    parser.add_argument("--output", "-o", default="news_output.json", help="Output file path (default: news_output.txt)")
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        print("Generating trending news information...")
        news_info = generate_trending_news_content(args.api_key)
        
        print("\n" + "="*50)
        print("TRENDING NEWS INFORMATION")
        print("="*50)

        print(f"TITLE: {news_info['title']}")

        print("\nDESCRIPTION:")
        print(news_info['description'])

        print("\nTAGS:")
        print(", ".join(news_info['tags']))

        print("="*50)

        if args.output.endswith('.json'):
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(news_info, f, ensure_ascii=False, indent=2)

    
    except Exception as e:
        print(f"Error generating trending news information: {e}")

if __name__ == "__main__":
    main()
    