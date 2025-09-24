#!/usr/bin/env python3
"""
Example script to score video segments and download the top k clips.
"""

from ..services.youtube_client import YouTubeClient
from ..services.llm.client import LLMClient
import os


def main():
    # Get video URL from user
    video_url = input("Enter YouTube video URL: ").strip()
    if not video_url:
        print("Error: URL cannot be empty.")
        return

    # Get number of clips to download
    try:
        k = int(input("Enter number of top clips to download (default: 5): ").strip() or "5")
    except ValueError:
        k = 5

    # Get segment duration
    try:
        segment_seconds = int(input("Enter segment duration in seconds (default: 60): ").strip() or "60")
    except ValueError:
        segment_seconds = 60

    print(f"\n🎬 Processing video: {video_url}")
    print(f"📥 Will download top {k} clips from {segment_seconds}-second segments")
    print("=" * 60)

    # Get video info first
    print("📊 Getting video information...")
    video_info = YouTubeClient.get_video_info(video_url)
    if video_info:
        print(f"Title: {video_info['title']}")
        print(f"Duration: {video_info['duration']} seconds")
        print(f"Uploader: {video_info['uploader']}")
    else:
        print("Could not get video info")
        return

    # Get transcript with segments
    print(f"\n📝 Extracting transcript with {segment_seconds}-second segments...")
    result = YouTubeClient.get_transcript_with_segments(video_url, segment_seconds=segment_seconds)

    if not result.transcript_result.success:
        print(f"❌ Failed to get transcript: {result.transcript_result.error_message}")
        return

    print(f"✅ Found {len(result.segments)} segments")
    print(f"📄 Full transcript length: {len(result.transcript_result.transcript)} characters")

    # Score all segments
    print(f"\n🤖 Scoring all {len(result.segments)} segments...")
    print("=" * 60)

    scored_segments = []
    total_scoring_time = 0

    for i, segment in enumerate(result.segments):
        print(f"📊 Scoring segment {i+1}/{len(result.segments)}...")
        
        # Combine all text from segment lines
        segment_text = " ".join([line.text for line in segment.lines])
        
        if not segment_text.strip():
            print(f"  ⚠️  Segment {i+1} is empty, skipping...")
            continue
        
        # Score the segment
        score = LLMClient.score_transcript(segment_text)
        
        if score is None:
            print(f"  ❌ Failed to score segment {i+1}")
            continue

        # Store segment with its score and metadata
        scored_segments.append({
            'segment_index': i,
            'start_time': segment.start,
            'end_time': segment.end,
            'text': segment_text[:100] + "..." if len(segment_text) > 100 else segment_text,
            'score': score,
            'overall_score': score.overall
        })

        total_scoring_time += score.scoring_duration
        print(f"  ✅ Segment {i+1}: {score.overall}/100 (took {score.scoring_duration:.2f}s)")

    if not scored_segments:
        print("❌ No segments were successfully scored.")
        return

    # Sort segments by overall score (highest first)
    scored_segments.sort(key=lambda x: x['overall_score'], reverse=True)

    # Download top k clips
    print(f"\n📥 Downloading top {k} clips...")
    print("=" * 60)

    # Create downloads directory
    os.makedirs("top_clips", exist_ok=True)
    
    downloaded_clips = []
    
    for i, segment in enumerate(scored_segments[:k]):
        try:
            # Create clip filename
            clip_filename = f"clip_{i+1}_{int(segment['start_time'])}s_{int(segment['end_time'])}s.mp4"
            clip_path = os.path.join("top_clips", clip_filename)
            
            print(f"📥 Downloading clip {i+1}/{k}: {clip_filename}")
            print(f"   ⏰ Time: {segment['start_time']:.1f}s - {segment['end_time']:.1f}s")
            print(f"   📊 Score: {segment['overall_score']:.1f}/100")
            
            # Download the segment
            success = YouTubeClient.download_video(
                video_url=video_url,
                output_path=clip_path,
                start_time=segment['start_time'],
                end_time=segment['end_time']
            )
            
            if success:
                # Get file size
                if os.path.exists(clip_path):
                    file_size = os.path.getsize(clip_path)
                    file_size_mb = file_size / (1024 * 1024)
                    
                    downloaded_clips.append({
                        'filename': clip_filename,
                        'path': clip_path,
                        'start_time': segment['start_time'],
                        'end_time': segment['end_time'],
                        'score': segment['overall_score'],
                        'file_size_mb': file_size_mb
                    })
                    
                    print(f"   ✅ Downloaded successfully ({file_size_mb:.2f} MB)")
                else:
                    print(f"   ❌ File not found after download")
            else:
                print(f"   ❌ Download failed")
                
        except Exception as e:
            print(f"   ❌ Error downloading clip {i+1}: {e}")
            continue

    # Display results
    print(f"\n🏆 DOWNLOAD RESULTS:")
    print("=" * 60)
    print(f"📊 Total clips downloaded: {len(downloaded_clips)}/{k}")
    print(f"⏱️  Total scoring time: {total_scoring_time:.2f} seconds")
    print()

    if downloaded_clips:
        for i, clip in enumerate(downloaded_clips):
            print(f"🥇 Clip #{i+1}")
            print(f"   📁 File: {clip['path']}")
            print(f"   📊 Score: {clip['score']:.1f}/100")
            print(f"   ⏱️  Time: {clip['start_time']:.1f}s - {clip['end_time']:.1f}s")
            print(f"   📦 Size: {clip['file_size_mb']:.2f} MB")
            print("-" * 60)

        # Show top 3 clips in detail
        print(f"\n🌟 TOP 3 CLIPS DETAILS:")
        print("=" * 60)
        for i, clip in enumerate(downloaded_clips[:3]):
            print(f"\n🥇 #{i+1} - {clip['filename']}")
            print(f"📁 File: {clip['path']}")
            print(f"📊 Score: {clip['score']:.1f}/100")
            print(f"⏱️  Time: {clip['start_time']:.1f}s - {clip['end_time']:.1f}s")
            print(f"📦 Size: {clip['file_size_mb']:.2f} MB")
            print("-" * 60)

        print(f"\n✅ Successfully downloaded {len(downloaded_clips)} clips!")
        print("💡 Next steps: Add watermarks and text overlays to these clips.")
        print(f"📁 Clips saved in: top_clips/")
    else:
        print("❌ No clips were successfully downloaded.")


if __name__ == "__main__":
    main()
