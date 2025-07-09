import os
import json
from diffusers import StableDiffusionPipeline
import torch
import concurrent.futures
from moviepy.editor import ImageSequenceClip

# --- CONFIGURATION ---
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")  # Hugging Face access token
NEWS_JSON = "news_output.json"
NUM_IMAGES = 1
IMAGE_PREFIX = "news_image_"

# --- 1. Load news description ---
with open(NEWS_JSON, "r", encoding="utf-8") as f:
    news = json.load(f)
description = news.get("description", "")
if not description:
    raise ValueError("No description found in news_output.json")

# --- 2. Load Stable Diffusion pipeline ---
print("Loading Stable Diffusion pipeline from Hugging Face...")
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    token=HF_TOKEN
)
pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")

# --- 3. Image generation function ---
def generate_image(prompt, idx):
    local_pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        token=HF_TOKEN
    )
    local_pipe = local_pipe.to("cuda" if torch.cuda.is_available() else "cpu")
    image = local_pipe(prompt, num_inference_steps=50).images[0]
    filename = f"news_image_{idx+1}.png"
    image.save(filename)
    return filename


# --- 4. Generate images in parallel ---
prompts = [description] * NUM_IMAGES  # Use the same description for all images
# with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_IMAGES) as executor:
#     futures = [
#         executor.submit(generate_image, prompt, idx)
#         for idx, prompt in enumerate(prompts)
#     ]
#     image_files = [future.result() for future in concurrent.futures.as_completed(futures)]
for idx, prompt in enumerate(prompts):
    image = pipe(prompt, num_inference_steps=50).images[0]
    filename = f"news_image_{idx+1}.png"
    image.save(filename)


# Sort image files in order (since as_completed may return out of order)
image_files = [f"{IMAGE_PREFIX}{i+1}.png" for i in range(NUM_IMAGES)]

# --- 5. Create transition video ---
print("Creating transition video from images...")
clip = ImageSequenceClip(image_files, durations=[2]*NUM_IMAGES)  # 2 seconds per image
clip = clip.crossfadein(1)  # 1 second crossfade between images
clip.write_videofile("news_transition_video.mp4", fps=24)
print("Video saved as news_transition_video.mp4")



"""
in this method, I am able to generate the images but there are several problems:
1) The hugging face module is downloading a massive 8gb file in chache memory, which is not ideal for a simple image generation task.
2) To generate single image it fetches 50 resource which take almost 30mins (due to less RAM and GPU), this is not ideal for a simple image generation task.
3) and so to generate multiple images it just crashes in between.
4) and therefore, this method is not suitable for generating multiple images in parallel.
"""