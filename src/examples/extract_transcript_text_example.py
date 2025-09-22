"""
YouTube transcript extraction example
"""

from ..services.youtube_client import YouTubeClient


def main():
    # Create YouTube client
    youtube_client = YouTubeClient()
    
    # Get YouTube video URL from user
    video_url = input("Enter YouTube video URL: ").strip()
    if not video_url:
        print("Error: URL cannot be empty!")
        return
    
    print(f"\nProcessing: {video_url}")
    
    # Get video information
    print("\nGetting video info...")
    info = youtube_client.get_video_info(video_url)
    if info:
        print(f"Title: {info['title']}")
        print(f"Duration: {info['duration']} seconds")
        print(f"Uploader: {info['uploader']}")
    else:
        print("Could not get video info")
        return
    
    # Extract transcript
    print("\nExtracting transcript...")
    result = youtube_client.get_transcript(video_url)
    
    if result.success:
        print(f"\nTranscript found! ({len(result.transcript)} characters)")
        print(f"Extraction took {result.duration:.2f} seconds")
        print("\n" + "="*50)
        print("TRANSCRIPT:")
        print("="*50)
        print(result.transcript)
        print("="*50)
        
    else:
        print(f"No transcript available for this video (took {result.duration:.2f} seconds)")
        if result.error_message:
            print(f"Error: {result.error_message}")
        print("This could be because:")
        print("- The video has no subtitles/captions")
        print("- The video is not in English")
        print("- The video is private or restricted")


if __name__ == "__main__":
    main()
