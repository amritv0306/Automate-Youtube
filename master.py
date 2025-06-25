import subprocess
import sys
import json
import time
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# --- LOGGING SETUP ---
LOG_FILE = "master_pipeline.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_step1(api_key, output_file="news_output.json"):
    logging.info("\n=== STEP 1: Generating Trending News ===")
    result = subprocess.run(
        [sys.executable, "step1.py", "--api-key", api_key, "--output", output_file],
        capture_output=True, text=True
    )
    logging.info(result.stdout)
    if result.returncode != 0:
        logging.error("Error in step1.py: %s", result.stderr)
        sys.exit(1)
    if not os.path.exists(output_file):
        logging.error("Error: %s not found after step1.py", output_file)
        sys.exit(1)
    with open(output_file, "r", encoding="utf-8") as f:
        news_info = json.load(f)
    return news_info

def run_step2(input_video, description, output_video):
    logging.info("\n=== STEP 2: Adding Captions and Speech to Video ===")
    result = subprocess.run(
        [
            sys.executable, "step2_new.py",
            "--video", input_video,
            "--text", description,
            "--output", output_video,
            # "--method", "subtitle"
        ],
        capture_output=True, text=True
    )
    logging.info(result.stdout)
    if result.returncode != 0:
        logging.error("Error in step2_new.py: %s", result.stderr)
        sys.exit(2)
    if not os.path.exists(output_video):
        logging.error("Error: %s not found after step2_new.py", output_video)
        sys.exit(2)
    return output_video

def run_step3(final_video, title, description, tags, client_secret="client_secret.json"):
    logging.info("\n=== STEP 3: Uploading Video to YouTube Shorts ===")
    tags_str = ",".join(tags)
    result = subprocess.run(
        [
            sys.executable, "step3.py",
            "--file", final_video,
            "--title", title,
            "--description", description,
            "--tags", tags_str,
            "--category", "22",
            "--privacy", "public"
        ],
        capture_output=True, text=True
    )
    logging.info(result.stdout)
    if result.returncode != 0:
        logging.error("Error in step3.py: %s", result.stderr)
        sys.exit(3)

def main():
    # ---- USER CONFIGURATION ----
    API_KEY = os.getenv("API_KEY")  # <-- Gemini API key here
    INPUT_VIDEO = "testvideo2.mp4"  # <-- input video file here
    FINAL_VIDEO = "final_output.mp4"
    NEWS_JSON = "news_output.json"
    # ----------------------------
    news_info = run_step1(API_KEY, output_file=NEWS_JSON)
    time.sleep(2)
    final_video_path = run_step2(INPUT_VIDEO, news_info["description"], FINAL_VIDEO)
    time.sleep(2)
    run_step3(
        final_video_path,
        news_info["title"],
        news_info["description"],
        news_info["tags"]
    )
    logging.info("=== ALL STEPS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
