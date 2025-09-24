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

### Twitch Chat Listening
```bash
python3 -m src.examples.twitch_chat_listener
```

### Ollama Chat Testing
```bash
python3 -m src.examples.ollama_chat_example
```

### YouTube Transcript with Segments
```bash
python3 -m src.examples.youtube_segments_example
```

### YouTube Video Chunk Scoring
```bash
python3 -m src.examples.score_video_chunks_example
```

### Download Top YouTube Clips (Scored & Downloaded)
```bash
python3 -m src.examples.download_top_clips_example
```

## Project Structure
```
clint/
├── src/
│   ├── services/          # API clients (Twitch, YouTube, LLM)
│   │   ├── llm/           # LLM service and prompts
│   │   ├── transcript_processor.py # Transcript extraction and segmentation
│   │   ├── twitch_client.py
│   │   └── youtube_client.py
│   └── examples/          # Example scripts
```

## Running Model Locally
1. Install ollama follow these instructions
2. Start the server by running: `ollama serve`
3. Pull the LLM model you'll want to test with. Example: `ollama pull llama3.1:8b`
4. Run the ollama chat example. Instructions can be found under `Ollama Chat Testing`


## Troubleshooting
If you get the following error: "Requested format is not available. Use --list-formats for a list of available formats" try updating the `yt-dlp` package by running: `python -m pip install -U yt-dlp`