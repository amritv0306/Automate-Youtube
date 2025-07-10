import subprocess
import sys
import json
import time
import os
import logging
from dotenv import load_dotenv
import random

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

def run_step1_1(gemini_api_key, newsdata_api_key, output_file="news_output.json"):
    logging.info("\n=== STEP 1: Generating Trending News using step1_1.py ===")
    result = subprocess.run(
        [
            sys.executable, "step1_1.py", # fle name changed from step1_1.py to step1_news_gen.py.
            "--gemini_api_key", gemini_api_key,
            "--newsdata_api_key", newsdata_api_key,
            "--output", output_file
        ],
        capture_output=True, text=True
    )
    logging.info(result.stdout)
    if result.returncode != 0:
        logging.info(f"Error in step1_1.py: {result.stderr}")
        sys.exit(1)
    if not os.path.exists(output_file):
        logging.error(f"Error: {output_file} not found after step1_1.py")
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

def run_step2_1(input_video, description, output_video, elevenlabs_api_key):
    logging.info("\n=== STEP 2: Adding Captions and Speech to Video ===")
    voices = {
        "Liam": "TX3LPaxmHKxFdv7VOQHJ",
        "Alice": "Xb7hH8MSUJpSbSDYk0k2",
        "Aria": "9BWtsMINqrJLrRacOk9x",
        "Bill": "pqHfZKP75CvOlQylNhV4",
        "Brian": "nPczCjzI2devNBz1zQrb",
        # "Grandpa": "NOpBlnGInO9m6vDvFkFC",
        "Mark": "UgBBYS2sOqTuMpoF3BR0",
        "Cassidy": "56AoDkrOh6qfVPDXZ7Pt"
    }
    voice_name = random.choice(list(voices.keys()))
    voice_id = voices[voice_name]
    logging.info("Selected voice: %s (ID: %s)", voice_name, voice_id)
    
    result = subprocess.run(
        [
            sys.executable, "step2_1.py", #file name changed from step2_1.py to step4_audio_caption.py.
            "--video", input_video,
            "--text", description,
            "--output", output_video,
            "--api_key", elevenlabs_api_key,
            "--voice_id", voice_id
        ],
        capture_output=True, text=True
    )
    logging.info(result.stdout)
    if result.returncode != 0:
        logging.error("Error in step2_1.py: %s", result.stderr)
        sys.exit(2)
    if not os.path.exists(output_video):
        logging.error("Error: %s not found after step2_1.py", output_video)
        sys.exit(2)
    return output_video

def run_step3(final_video, title, description, tags, client_secret="client_secret.json"):
    logging.info("\n=== STEP 3: Uploading Video to YouTube Shorts ===")
    tags_str = ",".join(tags)
    result = subprocess.run(
        [
            sys.executable, "step3.py", #file name changed from step3.py to step5_final_upload.py.
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
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
    INPUT_VIDEO = "testvideo2.mp4"
    FINAL_VIDEO = "final_output.mp4"
    NEWS_JSON = "news_output.json"
    # ----------------------------
    news_info = run_step1_1(GEMINI_API_KEY, NEWSDATA_API_KEY, output_file=NEWS_JSON)
    time.sleep(2)
    # final_video_path = run_step2(INPUT_VIDEO, news_info["description"], FINAL_VIDEO)
    final_video_path = run_step2_1(INPUT_VIDEO, news_info["description"], FINAL_VIDEO, ELEVENLABS_API_KEY)
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
