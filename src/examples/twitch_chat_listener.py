#!/usr/bin/env python3
"""
Twitch chat listening example
"""

import os
from dotenv import load_dotenv
from ..services.twitch_client import TwitchClient

def main():
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "your_client_id")
    ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN", "your_user_or_app_token")
    YOUR_CHANNEL_USERNAME = os.getenv("TWITCH_CHANNEL_USERNAME", "your_twitch_username")
    
    # Validate credentials
    if CLIENT_ID == "your_client_id" or ACCESS_TOKEN == "your_user_or_app_token":
        print("❌ Error: Please set up your .env file with valid Twitch credentials!")
        print("📝 See README.md for setup instructions.")
        return
    
    if YOUR_CHANNEL_USERNAME == "your_twitch_username":
        print("❌ Error: Please set TWITCH_CHANNEL_USERNAME in your .env file!")
        return
    
    # Get channel to listen to
    channel_username = input("Enter the Twitch channel username to listen to: ").strip()
    if not channel_username:
        print("❌ Error: Channel username cannot be empty!")
        return
    
    print(f"\n🔗 Connecting to #{channel_username}...")
    print("📝 Chat messages will appear below. Press Ctrl+C to stop.\n")
    
    try:
        # Create Twitch client and connect to chat
        twitch_client = TwitchClient(client_id=CLIENT_ID, access_token=ACCESS_TOKEN)
        twitch_client.listen_to_channel_messages(channel_username, YOUR_CHANNEL_USERNAME)
    except KeyboardInterrupt:
        print("\n👋 Disconnected from Twitch chat.")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting tips:")
        print("- Check your .env file has correct credentials")
        print("- Ensure your access token has 'user:read:chat' scope")
        print("- Verify the channel username is correct")

if __name__ == "__main__":
    main()
