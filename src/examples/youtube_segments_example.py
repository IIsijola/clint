"""
YouTube transcript + 60s segments example
"""

from ..services.youtube_client import YouTubeClient

def main():
    video_url = input("Enter YouTube video URL: ").strip()
    if not video_url:
        print("Error: URL cannot be empty!")
        return

    print("\nGetting transcript + segments...")
    combined = YouTubeClient.get_transcript_with_segments(video_url, segment_seconds=60)

    tr = combined.transcript_result
    if tr.success:
        print(f"\nTranscript (first 200 chars): {tr.transcript[:200]}...")
        print(f"Extraction took {tr.duration:.2f} seconds")
    else:
        print(f"Transcript not available ({tr.duration:.2f}s): {tr.error_message}")

    print("\nSegments (60s buckets):")
    if not combined.segments:
        print("No segments available")
    for seg in combined.segments:
        print(f"\nSegment {seg.index} [{seg.start:.1f}-{seg.end:.1f}s]")
        if not seg.lines:
            print("  (no lines in this window)")
        for line in seg.lines:
            print(f"  [{line.start:.1f}s] {line.text}")

if __name__ == "__main__":
    main()
