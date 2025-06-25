# import requests
# import json
# import argparse

# def get_top_headlines(api_key, country="in", max_results=1):
#     url = "https://newsapi.org/v2/top-headlines"
#     params = {
#         "country": country,
#         "pageSize": max_results,
#         "apiKey": api_key,
#         "language": "en"
#     }
#     response = requests.get(url, params=params)
#     data = response.json()
#     if data["status"] != "ok":
#         raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")
#     return data["articles"]

# def extract_news_metadata(article):
#     # You can customize this as needed
#     title = article.get("title", "No Title")
#     description = article.get("description", "") or article.get("content", "")
#     # Use title and description to generate tags (simple split, or use keywords)
#     tags = set()
#     for word in (title + " " + description).split():
#         word = word.strip(",.?!").capitalize()
#         if len(word) > 3:  # Only keep longer words for tags
#             tags.add(word)
#     tags = list(tags)[:10]  # Limit to 10 tags
#     return {
#         "title": title,
#         "description": description,
#         "tags": tags
#     }

# def main():
#     parser = argparse.ArgumentParser(description="Fetch trending news using NewsAPI")
#     parser.add_argument("--api-key", required=True, help="NewsAPI key")
#     parser.add_argument("--output", default="news_output.json", help="Output JSON file")
#     args = parser.parse_args()

#     articles = get_top_headlines(args.api_key, country="in", max_results=1)
#     if not articles:
#         print("No news articles found.")
#         return
    
#     print("Generating trending news information...")
#     news_info = extract_news_metadata(articles[0])

#     print("\n" + "="*50)
#     print("TRENDING NEWS INFORMATION")
#     print("="*50)

#     print(f"TITLE: {news_info['title']}")

#     print("\nDESCRIPTION:")
#     print(news_info['description'])

#     print("\nTAGS:")
#     print(", ".join(news_info['tags']))

#     print("="*50)

#     # Save to JSON for downstream steps
#     with open(args.output, "w", encoding="utf-8") as f:
#         json.dump(news_info, f, ensure_ascii=False, indent=2)
#     print(f"Saved trending news to {args.output}:\n{json.dumps(news_info, indent=2, ensure_ascii=False)}")

# if __name__ == "__main__":
#     main()

"""import requests

def fetch_trending_news_in_india(api_key, category=None, page_size=5):
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "in",          # 'in' for India
        "pageSize": page_size,    # number of articles to fetch
        "apiKey": api_key
    }

    if category:
        params["category"] = "technology"  # Optional: 'business', 'entertainment', etc.

    response = requests.get(url, params=params)
    data = response.json()
    print("Raw response:", data)  # Add this just after `data = response.json()`

    if data["status"] != "ok":
        print("Error:", data.get("message", "Unknown error"))
        return []

    articles = data["articles"]
    return [f"{article['title']} ({article['source']['name']})" for article in articles]

# Usage
api_key = "106200f63dd3441883c93c09ebc4559f"  # 🔑 Replace this with your actual NewsAPI key
news_list = fetch_trending_news_in_india(api_key, page_size=5)

if not news_list:
    print("No trending news found.")

for i, news in enumerate(news_list, 1):
    print(f"{i}. {news}")"""

import requests

def fetch_india_headlines(api_key):
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "in",
        "category": "general",  # Make sure category is added
        "pageSize": 5,
        "apiKey": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data["status"] != "ok":
        print("❌ Error:", data.get("message", "Unknown error"))
        return []

    articles = data.get("articles", [])
    if not articles:
        print("❗ No articles found. Try changing the category or removing filters.")
        return []

    print("📰 Top News Headlines in India:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']} ({article['source']['name']})")
    return articles

# 🔑 Replace this with your actual NewsAPI key
api_key = "106200f63dd3441883c93c09ebc4559f"

fetch_india_headlines(api_key)
print("✅ News headlines fetched successfully.")

