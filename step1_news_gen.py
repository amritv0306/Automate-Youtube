# getting the latest news headlines using NewsData.io and proccessing it through Gemini API to generate a YouTube video description, hashtags, and a hook.

import requests
import os
import json
import re
import time
from google import genai  # Gemini API client
from google.genai.types import GenerateContentConfig
import argparse

def gemini_generate(api_key, prompt, model="gemini-1.5-flash", retries=3, delay=2):
    client = genai.Client(api_key=api_key)
    system_instruction = """You are a helpful and professional content assistant specialized in optimizing YouTube video content. Your job is to generate concise, engaging, and YouTube-compliant content for creators. Follow YouTube's Community Guidelines strictly while avoiding hate speech, violence, adult content, or misleading claims.

    Your tasks include:
    1. Summarizing long video descriptions into ~100 words while keeping it informative, engaging, and compliant with YouTube's terms.
    2. Writing attention-grabbing video hooks based on a title or headline that encourage viewers to watch the video, without being clickbait or misleading.
    3. Generating relevant and trending hashtags related to the video's topic, using a mix of general and niche-specific tags, capped at 15.

    Maintain a neutral, informative tone, avoid sensationalism or controversial phrasing, and ensure the content is safe for general audiences.
    Output must be structured clearly for each task.
    ."""
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config = GenerateContentConfig(
                    system_instruction=system_instruction,
                ),
            )
            return response.text.strip()
        except Exception as e:
            if attempt == retries - 1:
                print(f"Gemini API failed after {retries} attempts: {e}")
                return None
            time.sleep(delay)

def fetch_top_news(api_key, country="in", language="en", limit=5):
    url = "https://newsdata.io/api/1/latest"
    params = {
        "apikey": api_key,
        "country": country,
        "language": language
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    # print(data)
    return data.get("results", [])[:limit]

def process_title_with_gemini(api_key, raw_title):
    prompt = (
        "You are a helpful assistant. "
        "Rewrite the following news headline to be a YouTube video title that strictly follows these rules:\n"
        "1. Must be under 100 characters.\n"
        "2. Use only plain ASCII characters (smart quotes, or non-English letters).\n"
        "3. Avoid using single (') or double (\") quotes unless absolutely necessary.\n"
        "4. The title must be clear and engaging for a general audience.\n"
        "5. Add an emoji at the end of the title to make it more engaging.\n"
        "6. Respond the revised title, nothing else.\n\n"
        f"Original headline:\n{raw_title}"
    )
    title = gemini_generate(api_key, prompt)
    # Ensure ASCII and length after Gemini
    import unicodedata
    title_ascii = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title_ascii = title_ascii.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
    # Remove quotes if present at start/end
    title_ascii = title_ascii.strip(' "\'')
    # Trim to 100 chars max
    if len(title_ascii) > 100:
        title_ascii = title_ascii[:100].rstrip()
    return title_ascii


def process_description(text, max_words=1000):
    words = (text or "").split()
    if len(words) > max_words:
        return " ".join(words[:max_words])
    return " ".join(words)

def generate_summary(api_key, text):
    prompt = f"""Summarize this text in exactly 100 words for a YouTube description that gains a lot of attention: {text}

    Rules:
    1. Keep strictly 100 words
    2. Use simple language
    3. Include key facts only and dont include hashtags
    4. Don't include any quotes. 
    5. Don't include \" or ' characters and its correspinding encodings like &quot; or &#39;"""
    return gemini_generate(api_key, prompt)

def generate_hashtags(api_key, text, num_tags=10):
    prompt = (
        f"Generate {num_tags} relevant, trending, and YouTube-compliant hashtags for the following video description. "
        "Return ONLY the hashtags as a Python list of strings, no explanations or extra text.\n\n"
        f"Description:\n{text}\n"
    )
    hashtags_text = gemini_generate(api_key, prompt)
    # Try to extract list from Gemini's output
    try:
        hashtags = eval(hashtags_text)
        if isinstance(hashtags, list):
            hashtags = [tag if tag.startswith("#") else "#" + tag.lstrip("#") for tag in hashtags]
            return hashtags[:num_tags]
    except Exception:
        # Fallback: extract hashtags with regex
        import re
        hashtags = re.findall(r"#\w+", hashtags_text)
        return hashtags[:num_tags]
    return []


def generate_hook(api_key, headline):
    prompt = f"""Convert this into a 5-word YouTube Shorts hook:
            Headline: '{headline}'
            Examples: 'This changes everything!', 'You won't believe this!'
            Respond ONLY with the hook."""
    hook = gemini_generate(api_key, prompt)
    return hook or "Must Watch! 🔥"

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Generate trending news information using Google Gemini API")
    
    # Add arguments
    parser.add_argument("--gemini_api_key", required=True, help="Google Gemini API key")
    parser.add_argument("--newsdata_api_key", required=True, help="Google Gemini API key")
    parser.add_argument("--output", "-o", default="news_output.json", help="Output file path (default: news_output.txt)")
    
    # Parse arguments
    args = parser.parse_args()

    print("Step 1.1: Fetching top 5 latest news from NewsData.io...")
    news_list = fetch_top_news(args.newsdata_api_key)
    if not news_list:
        print("No news fetched.")
        return

    print("\nFetched news headlines and description lengths:")
    for idx, n in enumerate(news_list, 1):
        desc_len = len((n.get('description') or '').split())
        # print(f"{idx}. {n.get('title', '')} | Description words: {desc_len}")
        print(f"{idx}. {n.get('title', '')} | Description words: {desc_len}".encode('ascii', errors='ignore').decode('ascii'))


    # Select the article with the longest description
    news_with_desc = [n for n in news_list if n.get("description")]
    if not news_with_desc:
        print("No news article with a valid description found.")
        return
    selected_news = max(news_with_desc, key=lambda n: len((n.get("description") or "").split()))

    print(f"\nSelected news with the longest description:\nTitle: {selected_news.get('title')}\nDescription length: {len(selected_news.get('description').split())} words")

    processed_title = process_title_with_gemini(args.gemini_api_key, selected_news.get("title", ""))

    description_raw = selected_news.get("description", "")
    description = process_description(description_raw, 1000)

    print("\nStep 1.2: Generating YouTube description with Gemini...")
    summary = generate_summary(args.gemini_api_key, description)
    if not summary:
        summary = description[:600]
    print(f"\nGenerated summary:\n{summary}")

    print("\nStep 1.3: Generating hashtags...")
    hashtags = generate_hashtags(args.gemini_api_key, description)
    print("Hashtags:", ", ".join(hashtags))

    print("\nStep 1.4: Generating YouTube hook with Gemini...")
    hook = generate_hook(args.gemini_api_key, selected_news.get("title", ""))
    print("Generated hook:", hook)

    output = {
        "title": processed_title,
        "description": summary,
        "tags": hashtags,
        "hook": hook
    }

    with open("news_output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\nAll done! Output saved to news_output.json")

if __name__ == "__main__":
    main()
