import subprocess
import sys
import json
import time
import os
import logging
from dotenv import load_dotenv
import random
import datetime

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

def run_with_retries(command, step_name, max_retries=3, delay=5):
    """Runs a command with a retry mechanism."""
    for attempt in range(max_retries):
        logging.info(f"--- Running {step_name}: Attempt {attempt + 1} of {max_retries} ---")
        # Use utf-8 encoding for cross-platform compatibility
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            logging.info(f"--- {step_name} completed successfully. ---")
            logging.info(result.stdout)
            return result

        logging.warning(f"--- {step_name} failed on attempt {attempt + 1}. Return code: {result.returncode} ---")
        logging.warning(f"Stderr: {result.stderr}")

        if attempt < max_retries - 1:
            logging.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
        else:
            logging.error(f"All {max_retries} attempts failed for {step_name}. Exiting pipeline.")
            sys.exit(1)

def run_step1(gemini_api_key, newsdata_api_key, output_file="news_output.json"):
    step_name = "STEP 1: Generating Trending News"
    command = [
        sys.executable, "step1_news_gen.py",
        "--gemini_api_key", gemini_api_key,
        "--newsdata_api_key", newsdata_api_key,
        "--output", output_file
    ]
    run_with_retries(command, step_name)

    if not os.path.exists(output_file):
        logging.error(f"Error: {output_file} not found after {step_name}")
        sys.exit(1)
    with open(output_file, "r", encoding="utf-8") as f:
        news_info = json.load(f)
    return news_info

def run_step2(gemini_api_key, imagerouter_api_key, news_file="news_output.json", save_folder="generated_images"):
    step_name = "STEP 2: Generating Images"
    command = [
        sys.executable, "step2_image_gen.py",
        "--gemini_api_key", gemini_api_key,
        "--imagerouter_api_key", imagerouter_api_key,
        "--news_file", news_file
    ]
    run_with_retries(command, step_name)

    if not os.path.exists(save_folder) or not os.listdir(save_folder):
        logging.error(f"Error: No images found in '{save_folder}' after {step_name}")
        sys.exit(1)
    logging.info(f"All images generated and saved to '{save_folder}'.")
    return save_folder

def run_step3(image_folder, output_video="temp_video_without_audio.mp4", video_duration=60, segment_duration=10):
    step_name = "STEP 3: Creating Video from Images"
    command = [
        sys.executable, "step3_video_gen.py",
        "--image_folder", image_folder,
        "--output_video", output_video,
        "--video_duration", str(video_duration),
        "--segment_duration", str(segment_duration)
    ]
    run_with_retries(command, step_name)

    if not os.path.exists(output_video):
        logging.error(f"Error: Video file '{output_video}' not found after {step_name}")
        sys.exit(1)
    logging.info(f"Video created and saved as '{output_video}'.")
    return output_video

def run_step4(input_video, description, output_video, elevenlabs_api_key):
    step_name = "STEP 4: Adding Captions and Speech"
    voices = {
        "Liam": "TX3LPaxmHKxFdv7VOQHJ",
        "Alice": "Xb7hH8MSUJpSbSDYk0k2",
        "Aria": "9BWtsMINqrJLrRacOk9x",
        "Bill": "pqHfZKP75CvOlQylNhV4",
        "Brian": "nPczCjzI2devNBz1zQrb",
        "Mark": "UgBBYS2sOqTuMpoF3BR0",
        "Cassidy": "56AoDkrOh6qfVPDXZ7Pt"
    }
    voice_name = random.choice(list(voices.keys()))
    voice_id = voices[voice_name]
    logging.info("Selected voice: %s (ID: %s)", voice_name, voice_id)
    
    command = [
        sys.executable, "step4_audio_caption.py",
        "--video", input_video,
        "--text", description,
        "--output", output_video,
        "--api_key", elevenlabs_api_key,
        "--voice_id", voice_id
    ]
    run_with_retries(command, step_name)

    if not os.path.exists(output_video):
        logging.error("Error: %s not found after %s", output_video, step_name)
        sys.exit(2)
    return output_video

def run_step5(final_video, title, description, tags, client_secret="client_secret.json"):
    step_name = "STEP 5: Uploading to YouTube"
    tags_str = ",".join(tags)
    command = [
        sys.executable, "step5_final_upload.py",
        "--file", final_video,
        "--title", title,
        "--description", description,
        "--tags", tags_str,
        "--category", "22",
        "--privacy", "public"
    ]

    run_with_retries(command, step_name)
    logging.info("YouTube upload process completed.")

def main():
    # ---- API Key Loading ----
    NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  
    IMAGEROUTER_API_KEY = os.getenv("IMAGEROUTER_API_KEY")

    # --- ElevenLabs Key Rotation Logic ---
    ELEVENLABS_API_KEY_1 = os.getenv("ELEVENLABS_API_KEY_1")
    ELEVENLABS_API_KEY_2 = os.getenv("ELEVENLABS_API_KEY_2")

    if not all([ELEVENLABS_API_KEY_1, ELEVENLABS_API_KEY_2]):
        logging.error("Both ELEVENLABS_API_KEY_1 and ELEVENLABS_API_KEY_2 must be set in the .env file.")
        sys.exit(1)

    current_day = datetime.datetime.now().day
    if 2 <= current_day <= 16:
        active_elevenlabs_key = ELEVENLABS_API_KEY_2
        key_using = 2
        # logging.info("Using ElevenLabs Key that resets on the 2nd (for days 2-16).")
    else:
        active_elevenlabs_key = ELEVENLABS_API_KEY_1
        key_using = 1
        # logging.info("Using ElevenLabs Key that resets on the 17th (for days 17-1).")

    NEWS_JSON = "news_output.json"
    FINAL_VIDEO = "final_output.mp4"

    news_info = run_step1(GEMINI_API_KEY, NEWSDATA_API_KEY, output_file=NEWS_JSON)
    time.sleep(2)

    generated_images_folder = run_step2(GEMINI_API_KEY, IMAGEROUTER_API_KEY, news_file=NEWS_JSON)
    time.sleep(2)

    generated_video = run_step3(image_folder=generated_images_folder)

    # Passing dynamically selected ElevenLabs key
    logging.info(f"Using ElevenLabs Key {key_using} for this run.")
    final_video = run_step4(generated_video, news_info["description"], FINAL_VIDEO, active_elevenlabs_key)
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
        logging.error("An unhandled error occurred in main: %s", str(e))
        sys.exit(1)