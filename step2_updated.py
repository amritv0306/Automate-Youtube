import os
import subprocess
import argparse
import pyttsx3
import torch
# used aeneas module earlier 
from ctc_forced_aligner import (
    load_audio,
    load_alignment_model,
    generate_emissions,
    preprocess_text,
    get_alignments,
    get_spans,
    postprocess_results,
)

os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"

def text_to_speech_with_voice(text, output_audio_path, voice_index=0, rate=180):
    """Convert text to speech using pyttsx3 with custom voice."""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    print("Available voices:")
    for idx, v in enumerate(voices):
        print(f"{idx}: {v.name} -> {v.id}")
    engine.setProperty('voice', voices[voice_index].id)
    engine.setProperty('rate', rate)
    engine.save_to_file(text, output_audio_path)
    engine.runAndWait()
    print(f"Speech audio saved to: {output_audio_path}")

def align_text_to_audio_ctc(audio_path, text, output_srt_path, language="eng"):
    """Align text to audio using ctc-forced-aligner and write SRT captions."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    alignment_model, alignment_tokenizer = load_alignment_model(
        device,
        dtype=torch.float16 if device == "cuda" else torch.float32,
    )
    audio_waveform = load_audio(audio_path, alignment_model.dtype, alignment_model.device)
    # Clean text (remove line breaks etc.)
    text_clean = " ".join(text.strip().split())
    emissions, stride = generate_emissions(alignment_model, audio_waveform)
    tokens_starred, text_starred = preprocess_text(
        text_clean,
        romanize=True,
        language=language,
    )
    segments, scores, blank_token = get_alignments(
        emissions,
        tokens_starred,
        alignment_tokenizer,
    )
    spans = get_spans(tokens_starred, segments, blank_token)
    word_timestamps = postprocess_results(text_starred, spans, stride, scores)
    # Write SRT
    with open(output_srt_path, "w", encoding="utf-8") as f:
        for i, (word, start, end, score) in enumerate(word_timestamps, 1):
            f.write(f"{i}\n")
            f.write(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
            f.write(f"{word}\n\n")
    print(f"Precise SRT captions saved to: {output_srt_path}")

def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def add_audio_and_live_captions_to_video(video_path, audio_path, srt_file, output_path):
    """Add audio and live captions to video using FFmpeg with subtitle file."""
    try:
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-vf', f"subtitles={srt_file}:force_style='Fontsize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2'",
            '-map', '0:v',
            '-map', '1:a',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'medium',
            '-shortest',
            '-y',
            output_path
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
        if os.path.exists(srt_file):
            os.remove(srt_file)

def main():
    parser = argparse.ArgumentParser(description="Add speech and live captions to a video from text (with precise alignment and custom voice)")
    parser.add_argument("--video", required=True, help="Path to input video file")
    parser.add_argument("--text", required=True, help="Text to convert to speech and add as live captions")
    parser.add_argument("--output", default="output_video.mp4", help="Path for output video file")
    parser.add_argument("--voice", type=int, default=0, help="Voice index for pyttsx3 (see list printed)")
    parser.add_argument("--rate", type=int, default=180, help="Speech rate for pyttsx3 (default: 180)")
    parser.add_argument("--language", type=str, default="eng", help="ISO-639-3 language code for alignment (default: eng)")
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Error: Input video file '{args.video}' not found.")
        return

    temp_audio_path = "temp_speech_audio.wav"
    temp_srt_path = "temp_precise_subtitles.srt"

    try:
        # Step 1: Convert text to speech with custom voice
        print("Converting text to speech with custom voice...")
        text_to_speech_with_voice(args.text, temp_audio_path, voice_index=args.voice, rate=args.rate)

        # Step 2: Use CTC forced aligner for precise captions
        print("Aligning text to audio for precise captions...")
        align_text_to_audio_ctc(temp_audio_path, args.text, temp_srt_path, language=args.language)

        # Step 3: Add audio and live captions to video
        success = add_audio_and_live_captions_to_video(args.video, temp_audio_path, temp_srt_path, args.output)

        if success:
            print("Process completed successfully!")
        else:
            print("Process failed!")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            print(f"Temporary audio file {temp_audio_path} removed.")

if __name__ == "__main__":
    main()
