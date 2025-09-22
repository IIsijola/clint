## Setup Instructions
1. Create a `.env` file. Instructions on how to get the `CLIENT_ID` and `ACCESS_TOKEN` below.
   ```
   TWITCH_CLIENT_ID=CLIENT_ID
   TWITCH_ACCESS_TOKEN=ACCESS_TOKEN
   TWITCH_CHANNEL_USERNAME=YOUR_USERNAME
   ```
2. Generate Access Token:
   - Go to this website: https://twitchtokengenerator.com/
   - Scroll down to `Generated Tokens`
   - Click `Bot Chat Token`
   - Click `Authorize`
   - Solve Captcha
   - Copy the two variables: `TWITCH_CLIENT_ID` and `TWITCH_ACCESS_TOKEN` to the `.env` file

## Examples

### YouTube Transcript Extraction
```bash
python3 -m src.examples.extract_transcript_text_example
```

### Twitch Chat Listening
```bash
python3 -m src.examples.twitch_chat_listener
```

## Project Structure
```
clint/
├── src/
│   ├── services/          # API clients (Twitch, YouTube)
│   └── examples/          # Example scripts
│       ├── extract_transcript_text_example.py
│       └── twitch_chat_listener.py
├── main.py               # Main application
├── examples.py           # Legacy Twitch examples
└── run_youtube_example.py # YouTube launcher
```

