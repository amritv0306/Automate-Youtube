# AutomateYoutube: Automated YouTube Shorts Pipeline

This project automates the creation and upload of YouTube Shorts videos using the latest news headlines, AI-generated images, synthesized speech, and captions. The pipeline consists of five main steps, each handled by a separate Python script, and a master script (`final_pipeline.py`) to run the entire process end-to-end.

## Table of Contents
- [Features](#features)
- [Pipeline Overview](#pipeline-overview)
- [Setup](#setup)
- [Step-by-Step Usage](#step-by-step-usage)
- [Master Pipeline](#master-pipeline)
- [Examples](#examples)
- [Notes](#notes)

---

## Features
- Fetches trending news headlines and generates YouTube-optimized metadata using Gemini API
- Generates AI images for video backgrounds
- Creates a video from shuffled images
- Synthesizes speech and generates captions using ElevenLabs and WhisperX
- Burns captions into the video and appends a custom ending image
- Uploads the final video as a YouTube Short

---

## Pipeline Overview

1. **step1_news_gen.py**: Fetches news and generates YouTube metadata (title, description, hashtags, hook) using Gemini API.
2. **step2_image_gen.py**: Generates AI images based on the news using Imagerouter.io and Gemini API.
3. **step3_video_gen.py**: Creates a video by shuffling and displaying the generated images.
4. **step4_audio_caption.py**: Synthesizes speech from text, adds it to the video, generates captions, burns them in, and appends an ending image.
5. **step5_final_upload.py**: Uploads the processed video to YouTube as a Short.
6. **final_pipeline.py**: Runs all steps above in sequence for full automation.

---

## Setup

1. **Clone the repository** and navigate to the project folder.
2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
3. **API Keys Required**:
   - Google Gemini API Key
   - NewsData.io API Key
   - Imagerouter.io API Key
   - ElevenLabs API Key & Voice ID
   - YouTube API credentials (client_secret.json, token.json)

4. **Directory Structure**:
   - `generated_images/` (stores generated images)
   - `pipeline_images/endingImgaeEnhanced.png` (ending image for video)

---

## Step-by-Step Usage

### 1. News Generation (step1_news_gen.py)
Fetches top news and generates YouTube metadata.
```powershell
python step1_news_gen.py --gemini_api_key <GEMINI_API_KEY> --newsdata_api_key <NEWSDATA_API_KEY>
```
- Output: `news_output.json` with title, description, hashtags, and hook.

### 2. Image Generation (step2_image_gen.py)
Generates images using Imagerouter.io and Gemini API.
```powershell
python step2_image_gen.py --gemini_api_key <GEMINI_API_KEY> --imagerouter_api_key <IMAGEROUTER_API_KEY>
```
- Output: Images saved in `generated_images/`

### 3. Video Generation (step3_video_gen.py)
Creates a video from the generated images.
```powershell
python step3_video_gen.py --image_folder generated_images --output_video random_shuffled_video.mp4 --video_duration 60 --segment_duration 10
```
- Output: `random_shuffled_video.mp4`

### 4. Audio & Caption (step4_audio_caption.py)
Synthesizes speech, adds it to the video, generates captions, burns them in, and appends an ending image.
```powershell
python step4_audio_caption.py --video random_shuffled_video.mp4 --text "<Your Text>" --api_key <ELEVENLABS_API_KEY> --voice_id <ELEVENLABS_VOICE_ID> --output final_output.mp4
```
- Output: `final_output.mp4` (with captions and ending image)

### 5. Upload to YouTube (step5_final_upload.py)
Uploads the final video as a YouTube Short.
```powershell
python step5_final_upload.py --file final_output.mp4 --title "<Title>" --description "<Description>" --tags "tag1,tag2,tag3" --category 22 --privacy public
```
- Output: Video uploaded to YouTube Shorts

---

## Master Pipeline

Run the entire process with one command:
```powershell
python final_pipeline.py
```
- This script orchestrates all steps above, using the required API keys and input files.

---

## Examples

### Example: Run All Steps Manually
```powershell
python step1_news_gen.py --gemini_api_key YOUR_GEMINI_KEY --newsdata_api_key YOUR_NEWSDATA_KEY
python step2_image_gen.py --gemini_api_key YOUR_GEMINI_KEY --imagerouter_api_key YOUR_IMAGEROUTER_KEY
python step3_video_gen.py --image_folder generated_images --output_video random_shuffled_video.mp4
python step4_audio_caption.py --video random_shuffled_video.mp4 --text "Breaking news!" --api_key YOUR_ELEVENLABS_KEY --voice_id YOUR_VOICE_ID
python step5_final_upload.py --file final_output.mp4 --title "Breaking News" --description "Latest updates" --tags "news,shorts,breaking" --category 22 --privacy public
```

### Example: Run Full Pipeline
```powershell
python final_pipeline.py
```

---

## Notes
- Ensure all API keys and credentials are set up before running the pipeline.
- The pipeline is designed for vertical, <=60s videos for YouTube Shorts.
- The ending image should be placed in `pipeline_images/endingImgaeEnhanced.png`.
- For YouTube upload, ensure `client_secret.json` and `token.json` are present and valid.

---

## License
MIT

---

## Contact
For questions or issues, please open an issue on GitHub or contact the project maintainer.
