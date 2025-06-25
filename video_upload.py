import os
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
# from google.oauth2.credentials import Credentials
from google import genai

# Constants
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "client_secret.json"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

def get_authenticated_service():
    """Authenticate and build the YouTube service."""
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=8080)
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def sanitize_youtube_metadata(text):
    # Remove angle brackets which are explicitly not allowed
    sanitized = text.replace('<', '').replace('>', '')
    # Remove or replace other potentially problematic characters
    # Trim whitespace
    sanitized = sanitized.strip()

    return sanitized

def generate_content(video_path, genai_api_key):
    """Generate video title, description and tags using Google Gemini."""
    # Configure the Gemini API client
    # genai.configure(api_key=genai_api_key)
    
    # Create a client
    client = genai.Client(api_key=genai_api_key)
    
    # Generate a title for the video
    title_prompt = f"Generate 1 catchy, SEO-friendly title for a video file named '{os.path.basename(video_path)}'. Keep it under 100 characters. Dont give options."
    title_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=title_prompt
    )
    
    # Generate a description for the video
    desc_prompt = f"Write a detailed, engaging description for a video file named '{os.path.basename(video_path)}'. Include relevant keywords and a call to action. Keep it under 5000 characters."
    desc_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=desc_prompt
    )
    
    # Generate tags for the video
    tags_prompt = f"Generate 10 relevant tags/keywords for a video file named '{os.path.basename(video_path)}'. Return them as a comma-separated list without numbering."
    tags_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=tags_prompt
    )
    
    # Extract and process the generated content
    # title = title_response.text.strip()
    title = sanitize_youtube_metadata(title_response.text)
    description = desc_response.text.strip()
    tags = [tag.strip() for tag in tags_response.text.split(',')]
    
    return title, description, tags


def upload_video(youtube, video_file, title, description, tags, category="22", privacy_status="private"):
    """Upload the video to YouTube."""
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }
    
    # Call the API's videos.insert method to create and upload the video
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )
    
    # The upload process
    print(f"Uploading file: {video_file}")
    response = None
    
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
    
    print(f"Upload Complete! Video ID: {response['id']}")
    return response['id']

def main():
    parser = argparse.ArgumentParser(description='Upload a video to YouTube with AI-generated metadata')
    parser.add_argument('--file', required=True, help='Path to the video file to upload')
    parser.add_argument('--genai-key', required=True, help='Google Gemini API key')
    parser.add_argument('--category', default='22', help='YouTube category ID (default: 22 - People & Blogs)')
    parser.add_argument('--privacy', default='private', choices=['private', 'public', 'unlisted'], 
                        help='Privacy status (default: private)')
    
    args = parser.parse_args()
    
    # Check if the video file exists
    if not os.path.exists(args.file):
        print(f"Error: Video file '{args.file}' does not exist.")
        return
    
    # Generate content using Google Gemini
    print("Generating video metadata using Google Gemini...")
    title, description, tags = generate_content(args.file, args.genai_key)
    
    print(f"Generated Title: {title}")
    print(f"Generated Tags: {', '.join(tags)}")
    print(f"Description length: {len(description)} characters")
    
    # Get authenticated YouTube service
    print("Authenticating with YouTube...")
    youtube = get_authenticated_service()
    
    # Upload the video
    video_id = upload_video(
        youtube, 
        args.file, 
        title, 
        description, 
        tags, 
        args.category, 
        args.privacy
    )
    
    print(f"Video uploaded successfully! YouTube URL: https://www.youtube.com/watch?v={video_id}")

if __name__ == "__main__":
    main()
