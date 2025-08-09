# Uploads a pre-processed video to YouTube as a "Short".
# This script takes title, description, and tags as command-line arguments.

import os
import argparse
from moviepy.editor import VideoFileClip
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow


# --- Constants ---
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
CLIENT_SECRETS_FILE = "client_secret.json" # Needed to refresh the token
TOKEN_FILE = "token.json" 


# --- Helper and Authentication Functions ---
def get_authenticated_service():
    """Gets valid user credentials from a token file or refreshes them."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, [ "https://www.googleapis.com/auth/youtube.upload"])
    
    # If there are no (valid) credentials available, something is wrong.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing access token...")
            creds.refresh(google.auth.transport.requests.Request())
            # Save the new credentials for the next run
            with open(TOKEN_FILE, 'w') as token_file:
                token_file.write(creds.to_json())
        else:
            # This should not happen on the server. It means the token is missing or invalid.
            print("Error: Could not find valid credentials. Please run '1_generate_token.py' locally first.")
            return None

    return build(API_SERVICE_NAME, API_VERSION, credentials=creds) 


# # --- Constants ---
# SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
# CLIENT_SECRETS_FILE = "client_secret.json"
# API_SERVICE_NAME = "youtube"
# API_VERSION = "v3"

# # --- Helper and Authentication Functions ---
# # to authanticate manually
# def get_authenticated_service():
#     """Authenticates the user and builds the YouTube API service object."""
#     flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
#     credentials = flow.run_local_server(port=8080)
#     return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)  




def get_video_duration(video_path):
    """Returns the duration of a video file in seconds using moviepy."""
    try:
        with VideoFileClip(video_path) as clip:
            return clip.duration
    except Exception as e:
        print(f"Error: Could not read video duration. Make sure moviepy is installed. Details: {e}")
        return -1


# --- YouTube Upload Function ---
def upload_video_as_short(youtube, video_file, title, description, tags, category, privacy_status):
    """Uploads a video file to YouTube with the specified metadata."""
    
    # --- YouTube Shorts Logic ---
    # 1. Ensure #Shorts is in the title for best visibility.
    if "#shorts" not in title.lower():
        title += " #Shorts"
        print("Appended #Shorts to title.")

    # 2. Ensure hastags is in the description.
    hashtags = " ".join(tag for tag in tags)
    # if "#shorts" not in description.lower():
    description += f"\n\n#Shorts {hashtags} #BreakingNews #India #Trending #Viral"
    print("Appended hastags to description.")

    # 3. Ensure 'shorts' is one of the tags.
    if "shorts" not in [tag.lower() for tag in tags]:
        tags.append("shorts")
        print("Added 'shorts' to tags.")
    
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

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    print(f"\nUploading file: {video_file}...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
    
    video_id = response.get('id')
    print(f"Upload Complete! Video ID: {video_id}")
    return video_id


# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description='Uploads a video to YouTube as a Short using provided metadata.')
    parser.add_argument('--file', required=True, help='Path to the video file to upload (must be <= 60s and vertical).')
    parser.add_argument('--title', required=True, help='The title of the video.')
    parser.add_argument('--description', required=True, help='The description of the video.')
    parser.add_argument('--tags', required=True, help='A comma-separated string of tags.')
    parser.add_argument('--category', default='22', help='YouTube category ID (default: 22 - People & Blogs).')
    parser.add_argument('--privacy', default='public', choices=['private', 'public', 'unlisted'], help='Privacy status (default: public).')
    args = parser.parse_args()

    # 1. Validate Video File
    if not os.path.exists(args.file):
        print(f"Error: Video file not found at '{args.file}'")
        return

    # 2. Check Video Duration for Shorts
    duration = get_video_duration(args.file)
    if duration == -1:
        return
        
    print(f"Validating video... Duration: {duration:.2f} seconds.")
    if duration > 60:
        print("Warning: Video is longer than 60 seconds. YouTube may not classify it as a Short.")
        # We still proceed with the upload as requested.

    # 3. Prepare Tags
    # Convert comma-separated string from argument to a list of strings
    tags_list = [tag.strip() for tag in args.tags.split(',')]

    # 4. Authenticate and Upload
    print("\nAuthenticating with YouTube...")
    youtube = get_authenticated_service()

    # hashtags = " ".join(tag for tag in args.tags)
    # final_description = args.description + "\n\n\n" + hashtags


    video_id = upload_video_as_short(
        youtube, args.file, args.title, args.description, tags_list, args.category, args.privacy
    )

    if video_id:
        print(f"\nVideo uploaded successfully! Watch your Short at: https://www.youtube.com/shorts/{video_id}")
    else:
        print("\nUpload failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
