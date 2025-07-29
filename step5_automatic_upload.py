# this script is for making the final upload process fully autonomous but this only works when the main user account is the part of google workspace account.
#refer below comments for more detail


import os
import argparse
from moviepy.editor import VideoFileClip
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- Constants ---
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
# The name of the JSON key file you downloaded
SERVICE_ACCOUNT_FILE = "fully_autonomous_client_secret.json"

# --- Helper and Authentication Function ---
def get_authenticated_service():
    """Authenticates using a service account and returns the YouTube API service."""
    # Actual Gmail account email
    DELEGATED_USER_EMAIL = "amritishoney@gmail.com"
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
        subject=DELEGATED_USER_EMAIL 
    )
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

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
    
    #1. Add #Shorts to the title and description for visibility
    if "#shorts" not in title.lower():
        title += " #Shorts"
        print("Appended #Shorts to title.")
    
    #2. Append hashtags to the description
    hashtags = " ".join(tag for tag in tags)
    description += f"\n\n#Shorts {hashtags} #BreakingNews #Trending #TheDailyPulse #Viral"
    print("Appended hastags to description.")

    #3. Ensure 'shorts' is one of the tags
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
    parser = argparse.ArgumentParser(description='Uploads a video to YouTube as a Short using a service account.')
    parser.add_argument('--file', required=True, help='Path to the video file to upload.')
    parser.add_argument('--title', required=True, help='The title of the video.')
    parser.add_argument('--description', required=True, help='The description of the video.')
    parser.add_argument('--tags', required=True, help='A comma-separated string of tags.')
    parser.add_argument('--category', default='25', help='YouTube category ID (default: 25 - News & Politics).')
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

    #3. Prepare Tags
    tags_list = [tag.strip() for tag in args.tags.split(',')]

    # 4. Authenticate and Upload
    print("\nAuthenticating with YouTube using service account...")
    youtube = get_authenticated_service()

    video_id = upload_video_as_short(
        youtube, args.file, args.title, args.description, tags_list, args.category, args.privacy
    )

    if video_id:
        print(f"\nVideo uploaded successfully! Watch it at: https://www.youtube.com/watch?v={video_id}")
    else:
        print("\nUpload failed. Please check the error messages above.")

if __name__ == "__main__":
    main()


# this script could be successfully runned on the email which a part of google workspace for e.g. your-name@your-company.com
# for more detail refer below understanding og Gemini
"""
This is the next, and often final, technical hurdle. The unauthorized_client error is very specific. It means your service account is correctly identifying itself, but it lacks the high-level administrative permission to act on behalf of your user account.

Think of it this way:

Step 1 (What you did): You made the service account an Editor on YouTube. This is like giving an employee a key to the building.

Step 2 (The missing part): You now need to give that employee the legal authority to sign documents on your behalf. This is a separate, higher-level permission configured in your Google domain, not on YouTube.

This permission is called Domain-Wide Delegation. The fix depends entirely on one crucial question:

Is your user account (your-email-here@gmail.com) a standard @gmail.com address, or is it part of a Google Workspace (e.g., your-name@your-company.com)?

Scenario 1: If you are using a Google Workspace Account (@yourcompany.com)
This is the scenario service account impersonation is designed for. You just need to enable the permissions in your Workspace Admin console.

Find Your Service Account's Unique ID:

Go to the Google Cloud Console Service Accounts page.

Click on the service account you created (daily-pulse-uploader).

Under the "Details" tab, find and copy the "Unique ID" number. It will be a long string of digits.

Go to your Google Workspace Admin Console:

You must be an administrator for your Workspace domain.

Navigate to admin.google.com.

Enable Domain-Wide Delegation:

In the Admin console, go to Security > Access and data control > API controls.

In the "Domain-wide Delegation" panel at the bottom, click "MANAGE DOMAIN WIDE DELEGATION".

Click "Add new".

In the Client ID field, paste the Unique ID of your service account that you copied in step 1.

In the OAuth scopes field, paste the exact scope your script needs:
https://www.googleapis.com/auth/youtube.upload

Click "AUTHORIZE".

After completing these steps, it may take anywhere from a few minutes to an hour for the settings to take effect. Once they do, your script will work.

Scenario 2: If you are using a Standard @gmail.com Account
This is the crucial part: Domain-Wide Delegation is a feature of Google Workspace and is not available for standard @gmail.com accounts. You cannot authorize a service account to impersonate a standard Gmail user in this way for the YouTube API.

If this is your situation, you must revert to a different authentication method. The most practical one is Method 2 from our earlier discussion: using a pre-generated refresh token.

This means you will have to:

Temporarily switch your step5 script back to the original version that used the browser-based flow (InstalledAppFlow).

Run it once locally to generate the token.json file.

Upload that token.json file to your server.

Modify the script to load credentials from that token.json file instead of trying to use a service account.

I know this feels like a step backward, but it is a firm limitation set by Google to protect personal accounts.

"""    