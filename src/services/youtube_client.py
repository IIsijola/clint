from .transcript_processor import (
    TranscriptProcessor, 
    TranscriptResult, 
    TranscriptLine, 
    TranscriptSegment, 
    TranscriptWithSegmentsResult
)
import yt_dlp
from typing import Optional, Dict, Any
import time


class YouTubeClient:
    """
    YouTube client for extracting video transcripts using yt-dlp.
    """
    
    @staticmethod
    def get_transcript(video_url: str) -> TranscriptResult:
        """
        Extract entire transcript from a YouTube video.

        Args:
            video_url (str): YouTube video URL or video ID

        Returns:
            TranscriptResult: Object containing transcript, duration, and success status
        """
        return TranscriptProcessor.get_transcript(video_url)

    @staticmethod
    def get_transcript_segments(video_url: str, segment_seconds: int = 60) -> list[TranscriptSegment]:
        """
        Extract timed transcript and group it into fixed-size segments.
        
        Args:
            video_url: YouTube video URL or ID
            segment_seconds: Segment duration in seconds (default: 60)
            
        Returns:
            List[TranscriptSegment]: Ordered segments with timed lines.
        """
        return TranscriptProcessor.get_transcript_segments(video_url, segment_seconds)

    @staticmethod
    def get_transcript_with_segments(video_url: str, segment_seconds: int = 60) -> TranscriptWithSegmentsResult:
        """
        Convenience method that returns both the cleaned transcript text and
        time-bucketed segments (default 60s) in a single call.
        """
        return TranscriptProcessor.get_transcript_with_segments(video_url, segment_seconds)
    
    @staticmethod
    def get_video_info(video_url: str) -> Optional[Dict[str, Any]]:
        """
        Get basic video information.
        
        Args:
            video_url (str): YouTube video URL or video ID
            
        Returns:
            Optional[Dict[str, Any]]: Video information if available
        """
        start_time = time.time()
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                result = {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'description': info.get('description'),
                }
                
                elapsed_time = time.time() - start_time
                print(f"[INFO] Video info retrieved in {elapsed_time:.2f} seconds")
                return result
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[ERROR] Failed to get video info after {elapsed_time:.2f} seconds: {e}")
            return None