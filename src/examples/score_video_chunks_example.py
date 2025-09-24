#!/usr/bin/env python3
"""
Example script to score all chunks of a YouTube video and sort them by score.
"""

from ..services.youtube_client import YouTubeClient
from ..services.llm.client import LLMClient, TranscriptScore


def main():
    # Get video URL from user
    video_url = input("Enter YouTube video URL: ").strip()
    if not video_url:
        print("Error: URL cannot be empty.")
        return

    print(f"\n🎬 Processing video: {video_url}")
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

    # Get transcript with 60-second segments
    print(f"\n📝 Extracting transcript with 60-second segments...")
    result = YouTubeClient.get_transcript_with_segments(video_url, segment_seconds=60)

    if not result.transcript_result.success:
        print(f"❌ Failed to get transcript: {result.transcript_result.error_message}")
        return

    print(f"✅ Found {len(result.segments)} segments")
    print(f"📄 Full transcript length: {len(result.transcript_result.transcript)} characters")
    print(f"⏱️  Extraction took: {result.transcript_result.duration:.2f} seconds")

    # Score each segment
    print(f"\n🤖 Scoring all {len(result.segments)} segments...")
    print("=" * 60)

    scored_segments = []
    total_scoring_time = 0

    for i, segment in enumerate(result.segments):
        # Combine all text from segment lines
        segment_text = " ".join([line.text for line in segment.lines])
        
        # Score the segment
        score: TranscriptScore = LLMClient.score_transcript(segment_text)
        
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

    # Display results
    print(f"\n🏆 TOP SCORING SEGMENTS (sorted by overall score):")
    print("=" * 60)
    print(f"📊 Total scoring time: {total_scoring_time:.2f} seconds")
    print(f"📈 Average scoring time per segment: {total_scoring_time/len(scored_segments):.2f} seconds")
    print()

    for i, segment_data in enumerate(scored_segments):
        score = segment_data['score']
        print(f"🥇 #{i+1} - Segment {segment_data['segment_index']+1}")
        print(f"   ⏰ Time: {segment_data['start_time']:.1f}s - {segment_data['end_time']:.1f}s")
        print(f"   📊 Overall: {score.overall}/100")
        print(f"   📝 Clarity: {score.clarity}/100")
        print(f"   🏗️  Structure: {score.structure}/100")
        print(f"   💡 Informativeness: {score.informativeness}/100")
        print(f"   🎯 Engagement: {score.engagement}/100")
        print(f"   ⚡ Pacing: {score.pacing}/100")
        print(f"   💭 Rationale: {score.rationale}")
        print(f"   📄 Text: {segment_data['text']}")
        print("-" * 60)

    # Summary statistics
    if scored_segments:
        scores = [s['overall_score'] for s in scored_segments]
        print(f"\n📈 SCORE STATISTICS:")
        print(f"   🎯 Highest score: {max(scores)}/100")
        print(f"   📉 Lowest score: {min(scores)}/100")
        print(f"   📊 Average score: {sum(scores)/len(scores):.1f}/100")
        print(f"   📊 Median score: {sorted(scores)[len(scores)//2]}/100")


if __name__ == "__main__":
    main()
