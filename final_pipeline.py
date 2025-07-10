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
LOG_FILE = "final_pipeline.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_step1(gemini_api_key, newsdata_api_key, output_file="news_output.json"):
    logging.info("\n=== STEP 1: Generating Trending News using step1_news_gen.py ===")
    result = subprocess.run(
        [
            sys.executable, "step1_news_gen.py",
            "--gemini_api_key", gemini_api_key,
            "--newsdata_api_key", newsdata_api_key,
            "--output", output_file
        ],
        capture_output=True, text=True
    )
    logging.info(result.stdout)
    if result.returncode != 0:
        logging.info(f"Error in step1_news_gen.py: {result.stderr}")
        sys.exit(1)
    if not os.path.exists(output_file):
        logging.error(f"Error: {output_file} not found after step1_news_gen.py")
        sys.exit(1)
    with open(output_file, "r", encoding="utf-8") as f:
        news_info = json.load(f)
    return news_info

def run_step2(gemini_api_key, imagerouter_api_key, news_file="news_output.json", save_folder="generated_images"):
    logging.info("\n=== STEP 2: Generating Images using News Description ===")
    result = subprocess.run(
        [
            sys.executable, "step2_image_gen.py",
            "--gemini_api_key", gemini_api_key,
            "--imagerouter_api_key", imagerouter_api_key,
            "--news_file", news_file
        ],
        capture_output=True, text=True
    )
    logging.info(result.stdout)
    if result.returncode != 0:
        logging.error(f"Error in step2_image_gen.py: {result.stderr}")
        sys.exit(1)
    if not os.path.exists(save_folder) or not os.listdir(save_folder):
        logging.error(f"Error: No images found in '{save_folder}' after step2_image_gen.py")
        sys.exit(1)
    logging.info(f"All images generated and saved to '{save_folder}'.")
    return save_folder

def run_step3(image_folder, output_video="temp_video_without_audio.mp4", video_duration=60, segment_duration=10):
    logging.info("\n=== STEP 3: Creating Video from Generated Images ===")
    result = subprocess.run(
        [
            sys.executable, "step3_video_gen.py",
            "--image_folder", image_folder,
            "--output_video", output_video,
            "--video_duration", str(video_duration),
            "--segment_duration", str(segment_duration)
        ],
        capture_output=True, text=True
    )
    logging.info(result.stdout)
    if result.returncode != 0:
        logging.error(f"Error in step3_video_gen.py: {result.stderr}")
        sys.exit(1)
    if not os.path.exists(output_video):
        logging.error(f"Error: Video file '{output_video}' not found after step3_video_gen.py")
        sys.exit(1)
    logging.info(f"Video created and saved as '{output_video}'.")
    return output_video

def run_step4(input_video, description, output_video, elevenlabs_api_key):
    logging.info("\n=== STEP 4: Adding Captions and Speech to Video ===")
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
            sys.executable, "step4_audio_caption.py",
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
        logging.error("Error in step4_audio_caption.py: %s", result.stderr)
        sys.exit(2)
    if not os.path.exists(output_video):
        logging.error("Error: %s not found after step4_audio_caption.py", output_video)
        sys.exit(2)
    return output_video

def run_step5(final_video, title, description, tags, client_secret="client_secret.json"):
    logging.info("\n=== STEP 5: Uploading Video to YouTube Shorts ===")
    tags_str = ",".join(tags)
    result = subprocess.run(
        [
            sys.executable, "step5_final_upload.py",
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
        logging.error("Error in step5_final_upload.py: %s", result.stderr)
        sys.exit(3) 

def main():
    # ---- USER CONFIGURATION ----
    NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  
    IMAGEROUTER_API_KEY = os.getenv("IMAGEROUTER_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    NEWS_JSON = "news_output.json"
    FINAL_VIDEO = "final_output.mp4"

    news_info = run_step1(GEMINI_API_KEY, NEWSDATA_API_KEY, output_file=NEWS_JSON)
    time.sleep(2)

    generated_images_folder = run_step2(GEMINI_API_KEY, IMAGEROUTER_API_KEY, news_file=NEWS_JSON)
    time.sleep(2)

    generated_video = run_step3(image_folder=generated_images_folder)

    final_video = run_step4(generated_video, news_info["description"], FINAL_VIDEO, ELEVENLABS_API_KEY)
    time.sleep(2)

    run_step5(
        final_video,
        news_info["title"],
        news_info["description"],
        news_info["tags"]
    )
    logging.info("=== ALL STEPS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        sys.exit(1)