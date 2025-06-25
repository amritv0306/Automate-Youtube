import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from moviepy.editor import ImageClip, concatenate_videoclips, CompositeVideoClip

def generate_images_gemini(api_key, prompt, n_images=5, out_dir="generated_images"):
    os.makedirs(out_dir, exist_ok=True)
    client = genai.Client(api_key=api_key)
    # Use Imagen 3 model for best quality, fallback to flash-preview if needed
    response = client.models.generate_images(
        model='imagen-3.0-generate-002',
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=n_images,
            aspect_ratio="16:9",  # or "1:1", "9:16" as needed
            # person_generation="allow_all"
        )
    )
    image_paths = []
    for i, generated_image in enumerate(response.generated_images, 1):
        img = Image.open(BytesIO(generated_image.image.image_bytes))
        img_path = os.path.join(out_dir, f"img_{i}.png")
        img.save(img_path)
        image_paths.append(img_path)
        print(f"Saved: {img_path}")
    return image_paths

def make_transition_video(image_paths, out_video="output_slideshow.mp4", total_duration=60, fps=24):
    n = len(image_paths)
    if n == 0:
        print("No images to make video.")
        return
    slide_duration = total_duration / n
    clips = [ImageClip(img).set_duration(slide_duration) for img in image_paths]

    # Add crossfade transitions of 1 second
    final = concatenate_videoclips(clips, method="compose", padding=-1, transition=lambda c1, c2: c2.crossfadein(1))
    final.write_videofile(out_video, fps=fps)
    print(f"Video saved as: {out_video}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate images with Gemini and create a transition video.")
    parser.add_argument("--api-key", required=True, help="Your Gemini API key")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--n-images", type=int, default=5, help="Number of images (default: 5)")
    parser.add_argument("--out-video", default="output_slideshow.mp4", help="Output video filename")
    args = parser.parse_args()

    print("Generating images...")
    image_paths = generate_images_gemini(args.api_key, args.prompt, args.n_images)
    print("Creating video slideshow...")
    make_transition_video(image_paths, args.out_video)
