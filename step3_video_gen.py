import os
import random
import argparse
from moviepy.editor import ImageClip, concatenate_videoclips

def get_image_files(image_folder):
    """Return a sorted list of image file paths from the given folder."""
    image_files = [
        os.path.join(image_folder, fname)
        for fname in os.listdir(image_folder)
        if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))
    ]
    image_files.sort()
    return image_files

def build_video_clips(image_files, video_duration, segment_duration):
    """
    Build a list of ImageClip objects for the video.
    Every segment_duration seconds, shuffle the image order.
    Each image is shown for 10 second.
    """
    num_images = len(image_files)
    num_segments = video_duration // segment_duration
    clips = []
    for seg in range(num_segments):
        random.shuffle(image_files)
        # Repeat images if needed to fill the segment
        images_for_segment = image_files * ((segment_duration + num_images - 1) // num_images)
        images_for_segment = images_for_segment[:segment_duration]
        for i in range(segment_duration):
            img_path = images_for_segment[i % num_images]
            clip = ImageClip(img_path).set_duration(10)
            clips.append(clip)
    return clips

def create_video_from_images(image_folder, output_video, video_duration=60, segment_duration=3):
    """
    Main function to create a video from shuffled images.
    """
    image_files = get_image_files(image_folder)
    num_images = len(image_files)
    print(f"Found {num_images} images in '{image_folder}'.")
    if num_images == 0:
        raise ValueError("No images found in the folder.")

    clips = build_video_clips(image_files, video_duration, segment_duration)
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip = final_clip.set_duration(video_duration)
    final_clip.write_videofile(output_video, fps=24)
    print(f"Video saved as {output_video}")

def main():
    parser = argparse.ArgumentParser(description="Create a 1-minute video from images, shuffling every 10 seconds.")
    parser.add_argument("--image_folder", default="generated_images", help="Folder containing images (default: generated_images)")
    parser.add_argument("--output_video", default="final_video.mp4", help="Output video filename (default: final_video.mp4)")
    parser.add_argument("--video_duration", type=int, default=60, help="Total video duration in seconds (default: 60)")
    parser.add_argument("--segment_duration", type=int, default=10, help="Shuffle order every N seconds (default: 10)")
    args = parser.parse_args()

    create_video_from_images(
        image_folder=args.image_folder,
        output_video=args.output_video,
        video_duration=args.video_duration,
        segment_duration=args.segment_duration
    )

if __name__ == "__main__":
    main()
