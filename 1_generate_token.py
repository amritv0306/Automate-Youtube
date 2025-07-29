# 1_generate_token.py
# generates a token for automatic user authantocation 
#it varifies singel time and later it varifies with the token generated.


import os
from google_auth_oauthlib.flow import InstalledAppFlow

# This is the scope your application requires to upload videos.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.json"

def generate_token():
    """Performs the browser-based authentication and saves the token."""
    print("Starting authentication flow...")
    if os.path.exists(TOKEN_FILE):
        print(f"'{TOKEN_FILE}' already exists. Delete it if you want to re-authenticate.")
        return

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)

    # This will open a browser window for you to log in and grant permissions.
    credentials = flow.run_local_server(port=8080)

    # Save the credentials for the next run
    with open(TOKEN_FILE, 'w') as token_file:
        token_file.write(credentials.to_json())

    print(f"\nAuthentication successful! Credentials saved to '{TOKEN_FILE}'.")
    print("You can now upload this file to your server along with your main scripts.")

if __name__ == "__main__":
    generate_token()