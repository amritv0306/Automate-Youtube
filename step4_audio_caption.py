import os
from elevenlabs import ElevenLabs
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips
import whisperx
import torch
import argparse
import subprocess


def text_to_speech_elevenlabs(text, output_audio_path, api_key, voice_id):
    client = ElevenLabs(api_key=api_key)
    audio_generator = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    with open(output_audio_path, "wb") as f:
        # f.write(audio)
        for chunk in audio_generator:
            if isinstance(chunk, bytes):
                f.write(chunk)
    print(f"Speech audio saved to: {output_audio_path}")

def add_audio_to_video(video_path, audio_path, output_path):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    video = video.subclip(0, audio.duration)
    final = video.set_audio(audio)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")
    print(f"Output video saved to: {output_path}")

def generate_srt_with_whisperx(audio_path, srt_path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisperx.load_model("small", device, compute_type="float32") # "large-v2" is the model name, you can change it to "base", "small", "medium", etc. based on your needs
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, language="en")
    model_a, metadata = whisperx.load_align_model(language_code="en", device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device)
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result["segments"], 1):
            start = seg["start"]
            end = seg["end"]
            text = seg["text"]
            f.write(f"{i}\n")
            f.write(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
            f.write(f"{text}\n\n")

def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def burn_captions_ffmpeg(video_path, srt_path, output_path):
    ffmpeg_cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='Fontsize=18,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2'",
        "-c:a", "copy", "-y", output_path
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"Final video with captions saved to: {output_path}")

def append_ending_image_to_video(main_video_path, ending_image_path, output_video_path, duration=2.5):
    # Load main video and ending image
    video = VideoFileClip(main_video_path)
    ending_clip = ImageClip(ending_image_path, duration=duration)
    ending_clip = ending_clip.set_duration(duration).set_fps(video.fps)
    try:
        ending_clip = ending_clip.resize(height=video.h)
    except Exception:
        pass
    # Concatenate video and ending image
    final = concatenate_videoclips([video, ending_clip], method="compose")
    final.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
    print(f"Appended ending image to create: {output_video_path}")

def main():
    parser = argparse.ArgumentParser(description="Add ElevenLabs speech and WhisperX captions to a video, with an ending image.")
    parser.add_argument("--video", required=True, help="Input video file")
    parser.add_argument("--text", required=True, help="Text to convert to speech")
    parser.add_argument("--output", default="final_output.mp4", help="Final output video file")
    
    parser.add_argument("--api_key", required=True, help="ElevenLabs API key")
    parser.add_argument("--voice_id", required=True, help="ElevenLabs voice ID")
    args = parser.parse_args()

    temp_audio = "temp_speech.mp3"
    temp_video = "temp_video_with_speech.mp4"
    temp_srt = "temp_captions.srt"
    intermediate_output = "final_no_ending.mp4"
    ending_image_path = os.path.join("pipeline_images", "endingImgaeEnhanced.png")

    # synthesize speech and add audio to video
    text_to_speech_elevenlabs(args.text, temp_audio, args.api_key, args.voice_id)
    add_audio_to_video(args.video, temp_audio, temp_video)
    generate_srt_with_whisperx(temp_audio, temp_srt)
    burn_captions_ffmpeg(temp_video, temp_srt, intermediate_output)

    # Append the ending image
    append_ending_image_to_video(intermediate_output, ending_image_path, args.output, duration=2.5)

    # Clean up
    for f in [temp_audio, temp_video, temp_srt, intermediate_output]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    main()
