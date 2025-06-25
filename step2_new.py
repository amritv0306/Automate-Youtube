# To add live captions and speech to the video

import os
from gtts import gTTS
import subprocess
import argparse
import re
import json

os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"

def text_to_speech_with_timing(text, output_audio_path):
    """Convert text to speech and estimate timing for each sentence"""
    # Split text into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Create TTS for the entire text
    tts = gTTS(text=text, lang='en')
    tts.save(output_audio_path)
    print(f"Speech audio saved to: {output_audio_path}")
    
    # Estimate timing for each sentence (rough approximation)
    # Average speaking rate is about 150 words per minute
    words_per_second = (150 / 60) - 1  # 2.5 words per second
    
    timing_data = []
    current_time = 0
    
    for sentence in sentences:
        word_count = len(sentence.split())
        duration = word_count / words_per_second
        
        timing_data.append({
            'text': sentence.strip(),
            'start': current_time,
            'end': current_time + duration
        })
        
        current_time += duration + 0.5  # Add small pause between sentences
    
    return timing_data

def create_subtitle_file(timing_data, subtitle_path):
    """Create an SRT subtitle file from timing data"""
    with open(subtitle_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(timing_data, 1):
            start_time = format_time(segment['start'])
            end_time = format_time(segment['end'])
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{segment['text']}\n\n")

def format_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def add_audio_and_live_captions_to_video(video_path, audio_path, timing_data, output_path):
    """Add audio and live captions to video using FFmpeg with subtitle file"""
    
    # Create subtitle file
    subtitle_file = "temp_subtitles.srt"
    create_subtitle_file(timing_data, subtitle_file)
    
    try:
        # Command to add audio and subtitles to video
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', video_path,        # Input video
            '-i', audio_path,        # Input audio
            '-vf', f"subtitles={subtitle_file}:force_style='Fontsize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2'",  # Add subtitles
            '-map', '0:v',           # Use video from first input
            '-map', '1:a',           # Use audio from second input
            '-c:v', 'libx264',       # Video codec
            '-c:a', 'aac',           # Audio codec
            '-preset', 'medium',     # Encoding preset
            '-shortest',             # End when shortest input ends
            '-y',                    # Overwrite output file
            output_path              # Output file
        ]

        print("Adding audio and live captions to video...")
        print(f"Running command: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        
        print(f"Output video saved to: {output_path}")
        return True
    
    finally:
        # Clean up subtitle file
        if os.path.exists(subtitle_file):
            os.remove(subtitle_file)

# def add_audio_and_animated_captions_to_video(video_path, audio_path, timing_data, output_path):
#     """Alternative method using drawtext with enable conditions for animated captions"""
    
#     # Build filter complex for animated captions
#     filter_parts = []
    
#     for i, segment in enumerate(timing_data):
#         start_time = segment['start']
#         end_time = segment['end']
#         text = segment['text'].replace("'", "\\'").replace(":", "\\:")
        
#         # Create a drawtext filter for each segment with time conditions
#         drawtext_filter = f"drawtext=text='{text}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=h-th-50:enable='between(t,{start_time},{end_time})'"
#         filter_parts.append(drawtext_filter)
    
#     # Combine all drawtext filters
#     video_filter = ','.join(filter_parts)
    
#     try:
#         ffmpeg_cmd = [
#             'ffmpeg',
#             '-i', video_path,
#             '-i', audio_path,
#             '-map', '0:v',
#             '-map', '1:a',
#             '-vf', video_filter,
#             '-c:v', 'libx264',
#             '-c:a', 'aac',
#             '-preset', 'medium',
#             '-shortest',
#             '-y',
#             output_path
#         ]

#         print("Adding audio and animated captions to video...")
#         result = subprocess.run(ffmpeg_cmd, stderr=subprocess.PIPE, text=True)

#         if result.returncode != 0:
#             print(f"Error: {result.stderr}")
#             return False
        
#         print(f"Output video saved to: {output_path}")
#         return True
    
#     except Exception as e:
#         print(f"Error in animated captions: {e}")
#         return False

def main():
    parser = argparse.ArgumentParser(description="Add speech and live captions to a video from text")
    parser.add_argument("--video", required=True, help="Path to input video file")
    parser.add_argument("--text", required=True, help="Text to convert to speech and add as live captions")
    parser.add_argument("--output", default="output_video.mp4", help="Path for output video file")
    # parser.add_argument("--method", choices=['subtitle', 'animated'], default='subtitle', help="Caption method: 'subtitle' uses SRT file, 'animated' uses drawtext filters")
    args = parser.parse_args()

    # Check if input video exists
    if not os.path.exists(args.video):
        print(f"Error: Input video file '{args.video}' not found.")
        return

    # Create temporary audio file
    temp_audio_path = "temp_speech_audio.mp3"

    try:
        # Step 1: Convert text to speech and get timing data
        print("Converting text to speech and calculating timing...")
        timing_data = text_to_speech_with_timing(args.text, temp_audio_path)
        
        print(f"Created {len(timing_data)} caption segments:")
        for i, segment in enumerate(timing_data, 1):
            print(f"  {i}. {segment['start']:.1f}s - {segment['end']:.1f}s: {segment['text']}")
        
        # Step 2: Add audio and live captions to video
        # if args.method == 'subtitle':
        success = add_audio_and_live_captions_to_video(args.video, temp_audio_path, timing_data, args.output)
        # else:
        #     success = add_audio_and_animated_captions_to_video(args.video, temp_audio_path, timing_data, args.output)
        
        if success:
            print("Process completed successfully!")
        else:
            print("Process failed!")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            print(f"Temporary audio file {temp_audio_path} removed.")

if __name__ == "__main__":
    main()
