# getting the latest news headlines using NewsData.io and proccessing it through Gemini API to generate a YouTube video description, hashtags, and a hook.

import requests
import os
import json
import re
import time
from google import genai  # Gemini API client
import argparse

def generate_hashtags(text, num_tags=10):
    stopwords = set([
        "the", "and", "for", "with", "that", "from", "this", "was", "are", "has", "had", "have",
        "but", "not", "out", "all", "can", "will", "his", "her", "their", "who", "what", "when",
        "where", "how", "why", "which", "about", "over", "into", "after", "just", "more", "than",
        "been", "they", "them", "you", "your", "our", "were", "she", "him", "its", "it's",
        "of", "on", "in", "to", "as", "by", "at", "is", "an", "a"
    ])
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = []
    seen = set()
    for word in words:
        if word not in stopwords and len(word) > 3 and word not in seen:
            keywords.append(word)
            seen.add(word)
    hashtags = ["#" + word for word in keywords[:num_tags]]
    while len(hashtags) < num_tags:
        hashtags.append(f"#news{len(hashtags)+1}")
    return hashtags

def gemini_generate(api_key, prompt, model="gemini-1.5-flash", retries=3, delay=2):
    client = genai.Client(api_key=api_key)
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
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
    return data.get("results", [])[:limit]

def process_description(text, max_words=1000):
    words = (text or "").split()
    if len(words) > max_words:
        return " ".join(words[:max_words])
    return " ".join(words)

def generate_summary(api_key, text):
    prompt = f"""Summarize this text in exactly 60 words for a YouTube description that gains a lot of attention:
{text}

Rules:
1. Keep strictly 100 words
2. Use simple language
3. Include key facts only"""
    return gemini_generate(api_key, prompt)

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
        print(f"{idx}. {n.get('title', '')} | Description words: {desc_len}")

    # Select the article with the longest description
    news_with_desc = [n for n in news_list if n.get("description")]
    if not news_with_desc:
        print("No news article with a valid description found.")
        return
    selected_news = max(news_with_desc, key=lambda n: len((n.get("description") or "").split()))

    print(f"\nSelected news with the longest description:\nTitle: {selected_news.get('title')}\nDescription length: {len(selected_news.get('description').split())} words")

    description_raw = selected_news.get("description", "")
    description = process_description(description_raw, 1000)

    print("\nStep 1.2: Generating YouTube description with Gemini...")
    summary = generate_summary(args.gemini_api_key, description)
    if not summary:
        summary = description[:600]
    print(f"\nGenerated summary:\n{summary}")

    print("\nStep 1.3: Generating hashtags...")
    hashtags = generate_hashtags(description)
    print("Hashtags:", ", ".join(hashtags))

    print("\nStep 1.4: Generating YouTube hook with Gemini...")
    hook = generate_hook(args.gemini_api_key, selected_news.get("title", ""))
    print("Generated hook:", hook)

    output = {
        "title": selected_news.get("title"),
        "description": summary,
        "tags": hashtags,
        "hook": hook
    }

    with open("news_output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\nAll done! Output saved to news_output.json")

if __name__ == "__main__":
    main()
