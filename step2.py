# To add the caption and sppech to the video

import os
from gtts import gTTS  # Google Text-To-Speech
import subprocess
import argparse
import tempfile
import shutil


os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"

def text_to_speech(text, output_audio_path):
    """Convert text to speech using Google Text-to-Speech"""
    tts = gTTS(text=text, lang='en')
    tts.save(output_audio_path)
    print(f"Speech audio saved to: {output_audio_path}")
    return output_audio_path

def normalize_text_for_ffmpeg(text):
    """Normalize text for FFmpeg drawtext filter based on search results"""
    return text.replace("\\", "\\\\")\
              .replace("'", "''")\
              .replace("%", "\\%")\
              .replace(":", "\\:")\
              .replace(",", "\\,")\
              .replace("{", "\\{")\
              .replace("}", "\\}")

def add_audio_and_captions_to_video(video_path, audio_path, caption_text, output_path):
    """
    Add audio and captions to video using FFmpeg
    Since MoviePy is having installation issues, we'll use FFmpeg directly
    """

    # Properly escape the caption text for shell
    # import shlex
    # escaped_caption = shlex.quote(caption_text)
    # escaped_caption = normalize_text_for_ffmpeg(caption_text)


    # font_path = "C:/Windows/fonts/arial.ttf"
    # font_path = "C\\:/Windows/Fonts/arial.ttf"
    # escaped_text_file = text_file.replace('\\', '/').replace('C:', 'C\\:')

    # Copy arial.ttf to current directory
    font_source = "C:/Windows/Fonts/arial.ttf"
    local_font = "arial.ttf"

    if not os.path.exists(local_font):
        try:
            shutil.copy2(font_source, local_font)
            print(f"Copied font to local directory: {local_font}")
        except:
            print("Could not copy font file. Using system font.")
            local_font = "arial"  # Use system font name

    text_file = "temp_caption.txt"
    try:
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(caption_text)

        # Create the drawtext filter string
        drawtext_filter = f"drawtext=fontfile={local_font}:textfile={text_file}:fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=h-th-10"


        # Command to add audio to video
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', video_path,            # Input video
            '-i', audio_path,            # Input audio
            '-map', '0:v',               # Use video from first input
            '-map', '1:a',               # Use audio from second input
            '-vf', drawtext_filter,  # Add caption
            '-c:v', 'libx264',           # Use H.264 codec instead of copy
            '-c:a', 'aac',
            # 'crf', '23',                 # Quality setting (lower = better quality)
            '-preset', 'medium',         # Encoding speed/compression tradeoff
            '-shortest',                 # End when shortest input ends
            '-f', 'mp4',                 # Explicitly specify output format
            '-y',                        # Overwrite output file if it exists
            output_path                  # Output file
        ]
        
        print("Adding audio and captions to video...")
        print(f"Running command: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, stderr=subprocess.PIPE, text=True)
        # subprocess.run(ffmpeg_cmd)  
        # print(f"Output video saved to: {output_path}")
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        
        print(f"Output video saved to: {output_path}")
        return True
    
    finally:
        # Clean up the temporary text file
        if os.path.exists(text_file):
            os.remove(text_file)

def main():
    parser = argparse.ArgumentParser(description="Add speech and captions to a video from text")
    parser.add_argument("--video", required=True, help="Path to input video file")
    parser.add_argument("--text", required=True, help="Text to convert to speech and add as caption")
    parser.add_argument("--output", default="output_video.mp4", help="Path for output video file")
    args = parser.parse_args()
    
    # Check if input video exists
    if not os.path.exists(args.video):
        print(f"Error: Input video file '{args.video}' not found.")
        return
    
    # Create temporary audio file
    temp_audio_path = "temp_speech_audio.mp3"
    
    try:
        # Step 1: Convert text to speech
        text_to_speech(args.text, temp_audio_path)
        
        # Step 2: Add audio and captions to video
        add_audio_and_captions_to_video(args.video, temp_audio_path, args.text, args.output)
        
        print("Process completed successfully!")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            print(f"Temporary audio file {temp_audio_path} removed.")

if __name__ == "__main__":
    main()
