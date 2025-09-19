import os
from dotenv import load_dotenv
from twitch_client import TwitchClient

# Load env variables
load_dotenv()
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "your_client_id")
ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN", "your_user_or_app_token")
YOUR_CHANNEL_USERNAME = os.getenv("TWITCH_CHANNEL_USERNAME", "your_twitch_username")

# Ask for channel username
CHANNEL_USERNAME = input("Enter the Twitch channel username to listen to: ").strip()
if not CHANNEL_USERNAME:
    print("Error: Channel username cannot be empty!")
    exit(1)

# Create Twitch client and connect to chat
twitch_client = TwitchClient(client_id=CLIENT_ID, access_token=ACCESS_TOKEN)
twitch_client.listen_to_channel_messages(CHANNEL_USERNAME, "heaverage")
