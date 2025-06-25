"""tags = ["#AirIndiaExpress", "#TyreBurst", "#AhmedabadAirport", "#EmergencyLanding", "#FlightSafety", "#AviationIncident", "#PassengersSafe", "#Boeing737", "#DGCAInvestigation", "#TravelDisruption"]

print(tags)

hashtags = " ".join(tag for tag in tags)

print(f"Generated Tags: {hashtags}")"""


from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="sk_acddcb900a3b8b687eb6926bd9f09ef14f975ca5c3d71865")
audio_generator  = client.text_to_speech.convert(
    # text="A young woman named Anya discovers an antique locket during a renovation project. Intrigued, she opens it and finds a faded photograph and a handwritten note. The note reveals a secret love affair and a hidden treasure. Anya, compelled by the mystery, embarks on a quest to find the treasure, following cryptic clues hidden within the photograph and the note.",
    text = "A severe heatwave is gripping much of India, triggering health alerts and impacting daily life. Temperatures are soaring, reaching record highs in several states, prompting advisories for vulnerable populations. Water scarcity is worsening, and power grids are strained. The government is urging citizens to take precautions, stay hydrated, and avoid outdoor activities during peak heat hours. Concerns are mounting regarding the potential impact on agriculture and the risk of heatstroke-related fatalities. Relief is not expected immediately, with forecasts predicting continued high temperatures for the coming days.",
    voice_id="TX3LPaxmHKxFdv7VOQHJ",
    model_id="eleven_multilingual_v2",  # or another supported model
    output_format="mp3_44100_128",
)

with open("output_audio.mp3", "wb") as f:
    for chunk in audio_generator:
        if isinstance(chunk, bytes):
            f.write(chunk)
    print("Audio saved to output_audio.mp3")


"""from moviepy.editor import VideoFileClip, AudioFileClip

video = VideoFileClip("testvideo2.mp4")
audio = AudioFileClip("output_audio.mp3").set_duration(video.duration)
final = video.set_audio(audio)
final.write_videofile("video_with_speech.mp4", codec="libx264", audio_codec="aac")"""


"""import whisperx
import torch

def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisperx.load_model("large-v2", device, compute_type="float32")
audio = whisperx.load_audio("output_audio.mp3")
result = model.transcribe(audio)
model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
result = whisperx.align(result["segments"], model_a, metadata, audio, device)
# Write SRT
with open("output_captions.srt", "w", encoding="utf-8") as f:
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

print(f"Precise SRT captions saved to: output_captions.srt")"""