import requests
import argparse
import json
import time

def get_latest_news(api_key, max_retries=3):
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "in",
        "apiKey": api_key,
        "pageSize": 1,
        "sortBy": "publishedAt"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # Raise HTTP errors
            data = response.json()
            
            if not data.get("articles"):
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retrying
                    continue
                raise ValueError("No articles found in NewsAPI response.")
            
            article = data["articles"][0]
            return {
                "title": article["title"].replace('"', ''),
                "description": article.get("description") or article["title"],
                "tags": ["#BreakingNews", "#India"]
            }
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"NewsAPI failed after {max_retries} retries: {str(e)}")
            time.sleep(2)

from bs4 import BeautifulSoup

def scrape_google_news():
    url = "https://news.google.com/topstories?hl=en-IN&gl=IN&ceid=IN:en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Updated selector (June 2024)
        headline_element = soup.select_one("h3 a")  # More generic selector
        print(headline_element) # Debugging line to check if the element is found
        if not headline_element:
            raise ValueError("No headlines found on Google News.")
        
        return {
            "title": headline_element.text.strip(),
            "description": "Latest trending news from Google",  # Fallback
            "tags": ["#Trending", "#India"]
        }
        
    except Exception as e:
        raise Exception(f"Google News scraping failed: {str(e)}")
    
news_data = scrape_google_news()
output = "news_data.json"
with open(output, "w") as f:
    json.dump(news_data, f, indent=2)
    

    
# def get_news_safely(api_key):
#     try:
#         return get_latest_news(api_key)  # Try NewsAPI first
#     except Exception as api_error:
#         print(f"NewsAPI failed: {api_error}. Falling back to scraping...")
#         try:
#             return scrape_google_news()  # Fallback to scraping
#         except Exception as scrape_error:
#             raise Exception(f"All news sources failed:\n1. {api_error}\n2. {scrape_error}")

# # Usage:

# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--api-key", required=True, help="NewsAPI key")
#     parser.add_argument("--output", default="news_output_new.json", help="Output file")
#     args = parser.parse_args()

#     # news_data = get_latest_news(args.api_key)
#     news_data = get_news_safely(args.api_key)    
#     # news_data = scrape_google_news()
#     with open(args.output, "w") as f:
#         json.dump(news_data, f, indent=2)


# if __name__ == "__main__":
#     main()
