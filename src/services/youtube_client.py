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
import os


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

    @staticmethod
    def download_video(video_url: str, 
                      output_path: str,
                      start_time: Optional[float] = None,
                      end_time: Optional[float] = None,
                      quality: str = "best[height<=1080]/best[height<=720]/best[height<=480]/best") -> bool:
        """
        Download a YouTube video or video segment.
        
        Args:
            video_url (str): YouTube video URL or video ID
            output_path (str): Output file path (including filename and extension)
            start_time (float, optional): Start time in seconds. If None, starts from beginning
            end_time (float, optional): End time in seconds. If None, ends at video end
            quality (str): Video quality preference (default: 1080p → 720p → 480p → best)
            
        Returns:
            bool: True if successful, False otherwise
            
        Examples:
            # Download entire video
            YouTubeClient.download_video("https://youtube.com/watch?v=example", "video.mp4")
            
            # Download from 30 seconds to end
            YouTubeClient.download_video("https://youtube.com/watch?v=example", "clip.mp4", start_time=30)
            
            # Download from 0 to 60 seconds
            YouTubeClient.download_video("https://youtube.com/watch?v=example", "clip.mp4", end_time=60)
            
            # Download specific segment (30s to 90s)
            YouTubeClient.download_video("https://youtube.com/watch?v=example", "clip.mp4", start_time=30, end_time=90)
        """
        start_download_time = time.time()
        
        try:
            # Get video info first to validate the URL and get duration
            video_info = YouTubeClient.get_video_info(video_url)
            if not video_info:
                print(f"[ERROR] Could not get video info for: {video_url}")
                return False
            
            video_duration = video_info.get('duration', 0)
            
            # Validate and adjust timing parameters
            if start_time is None:
                start_time = 0.0
            if end_time is None:
                end_time = video_duration
                
            # Ensure start_time is not negative
            start_time = max(0.0, start_time)
            
            # Ensure end_time doesn't exceed video duration
            end_time = min(end_time, video_duration)
            
            # Ensure start_time < end_time
            if start_time >= end_time:
                print(f"[ERROR] Invalid time range: start_time ({start_time}s) >= end_time ({end_time}s)")
                return False
            
            duration = end_time - start_time
            print(f"[INFO] Downloading segment: {start_time}s to {end_time}s (duration: {duration}s)")
            
            # Configure yt-dlp options
            # Quality format: 1080p → 720p → 480p → best available
            ydl_opts = {
                'format': quality,
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
            }
            
            # Add timing parameters if not downloading the entire video
            if start_time > 0 or end_time < video_duration:
                ydl_opts['external_downloader'] = 'ffmpeg'
                ydl_opts['external_downloader_args'] = [
                    '-ss', str(start_time),
                    '-t', str(duration)
                ]
            
            # Download the video
            print(f"[INFO] Starting download to: {output_path}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            elapsed_time = time.time() - start_download_time
            print(f"[INFO] Download completed in {elapsed_time:.2f} seconds")
            return True
            
        except Exception as e:
            elapsed_time = time.time() - start_download_time
            print(f"[ERROR] Download failed after {elapsed_time:.2f} seconds: {e}")
            return False