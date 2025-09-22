# youtube_client.py
# YouTube transcript extraction using yt-dlp

import yt_dlp
from typing import Optional, List, Dict, Any
import re
import time
from dataclasses import dataclass


@dataclass
class TranscriptResult:
    """
    Result object containing transcript and duration information.
    """
    transcript: str
    duration: float  # Duration in seconds
    success: bool
    error_message: Optional[str] = None


class YouTubeClient:
    """
    YouTube client for extracting video transcripts using yt-dlp.
    """
    
    def __init__(self):
        """Initialize the YouTube client."""
        pass
    
    def get_transcript(self, video_url: str) -> TranscriptResult:
        """
        Extract transcript from a YouTube video.

        Args:
            video_url (str): YouTube video URL or video ID

        Returns:
            TranscriptResult: Object containing transcript, duration, and success status

        Requirements: yt-dlp package
        """
        start_time = time.time()
        
        try:
            # Configure yt-dlp options for transcript extraction
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en', 'en-US', 'en-GB'],  # Try English variants first
                'skip_download': True,  # We only want the transcript, not the video
                'quiet': True,  # Enable output for debugging
                'no_warnings': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info
                print(f"[DEBUG] Extracting info for: {video_url}")
                info = ydl.extract_info(video_url, download=False)
                
                # Try to get subtitles/transcript
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})
                
                print(f"[DEBUG] Found subtitles: {list(subtitles.keys())}")
                
                # Combine both subtitle sources
                all_subtitles = {**subtitles, **automatic_captions}
                
                if not all_subtitles:
                    print("[DEBUG] No subtitles or captions found")
                    return None
                
                # Try to find English subtitles
                transcript_text = self._extract_transcript_text(all_subtitles, ydl)
                
                if transcript_text:
                    print(f"[DEBUG] Extracted transcript length: {len(transcript_text)} characters")
                    cleaned_transcript = self._clean_transcript(transcript_text)
                    elapsed_time = time.time() - start_time
                    print(f"[INFO] Transcript extraction completed in {elapsed_time:.2f} seconds")
                    return TranscriptResult(
                        transcript=cleaned_transcript,
                        duration=elapsed_time,
                        success=True
                    )
                else:
                    print("[DEBUG] No transcript text extracted")
                    elapsed_time = time.time() - start_time
                    print(f"[INFO] No transcript found after {elapsed_time:.2f} seconds")
                    return TranscriptResult(
                        transcript="",
                        duration=elapsed_time,
                        success=False,
                        error_message="No transcript available for this video"
                    )
                    
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[ERROR] Failed to extract transcript after {elapsed_time:.2f} seconds: {e}")
            return TranscriptResult(
                transcript="",
                duration=elapsed_time,
                success=False,
                error_message=str(e)
            )
    
    def _extract_transcript_text(self, subtitles: Dict[str, Any], ydl) -> Optional[str]:
        """
        Extract transcript text from subtitle data.
        
        Args:
            subtitles: Subtitle data from yt-dlp
            ydl: yt-dlp instance
            
        Returns:
            Optional[str]: Extracted transcript text
        """
        # Try different language codes
        lang_codes = ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU']
        
        for lang in lang_codes:
            if lang in subtitles:
                print(f"[DEBUG] Trying language: {lang}")
                subtitle_data = subtitles[lang]
                if subtitle_data:
                    print(f"[DEBUG] Found {len(subtitle_data)} subtitle formats for {lang}")
                    # Get the first available format
                    for i, sub_format in enumerate(subtitle_data):
                        try:
                            # Download and extract subtitle content
                            subtitle_url = sub_format['url']
                            transcript = ydl.urlopen(subtitle_url).read().decode('utf-8')
                            
                            # Parse the transcript based on format
                            if 'vtt' in sub_format.get('ext', '').lower():
                                parsed = self._parse_vtt(transcript)
                                if parsed:
                                    print(f"[DEBUG] VTT parsing successful, length: {len(parsed)}")
                                    return parsed
                            elif 'srv' in sub_format.get('ext', '').lower():
                                parsed = self._parse_srv(transcript)
                                if parsed:
                                    print(f"[DEBUG] SRV parsing successful, length: {len(parsed)}")
                                    return parsed
                            elif 'json' in sub_format.get('ext', '').lower():
                                parsed = self._parse_json3(transcript)
                                if parsed:
                                    print(f"[DEBUG] JSON3 parsing successful, length: {len(parsed)}")
                                    return parsed
                            else:
                                # Try to parse as plain text
                                parsed = self._parse_plain_text(transcript)
                                if parsed:
                                    print(f"[DEBUG] Plain text parsing successful, length: {len(parsed)}")
                                    return parsed
                                
                        except Exception as e:
                            print(f"[DEBUG] Failed to process format {i+1}: {e}")
                            continue
        
        # If no English subtitles found, try any available language
        print("[DEBUG] No English subtitles found, trying any available language...")
        for lang, subtitle_data in subtitles.items():
            if subtitle_data:
                for i, sub_format in enumerate(subtitle_data):
                    try:
                        subtitle_url = sub_format['url']
                        transcript = ydl.urlopen(subtitle_url).read().decode('utf-8')
                        
                        # Parse the transcript based on format
                        if 'vtt' in sub_format.get('ext', '').lower():
                            parsed = self._parse_vtt(transcript)
                            if parsed:
                                return parsed
                        elif 'srv' in sub_format.get('ext', '').lower():
                            parsed = self._parse_srv(transcript)
                            if parsed:
                                return parsed
                        else:
                            parsed = self._parse_plain_text(transcript)
                            if parsed:
                                return parsed
                                
                    except Exception as e:
                        print(f"[DEBUG] Parsing transcript failed: {e}")
                        continue
        
        return None
    
    def _parse_json3(self, json_content: str) -> str:
        """
        Parse JSON3 subtitle format (YouTube's internal format).
        
        Args:
            json_content: JSON3 subtitle content
            
        Returns:
            str: Parsed transcript text
        """
        import json
        
        try:
            data = json.loads(json_content)
            transcript_parts = []
            
            # Extract text from events
            if 'events' in data:
                for event in data['events']:
                    if 'segs' in event:
                        for seg in event['segs']:
                            if 'utf8' in seg:
                                transcript_parts.append(seg['utf8'])
            
            result = ' '.join(transcript_parts)
            return result
            
        except Exception as e:
            print(f"[DEBUG] JSON3 parsing failed: {e}")
            return ""
    
    def _parse_vtt(self, vtt_content: str) -> str:
        """
        Parse VTT (WebVTT) subtitle format.
        
        Args:
            vtt_content: VTT subtitle content
            
        Returns:
            str: Parsed transcript text
        """
        lines = vtt_content.split('\n')
        transcript_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip VTT headers, timestamps, and empty lines
            if (line and 
                not line.startswith('WEBVTT') and 
                not line.startswith('NOTE') and
                not '-->' in line and
                not line.isdigit() and
                not re.match(r'^\d+$', line) and  # Skip line numbers
                not re.match(r'^\d{2}:\d{2}:\d{2}', line)):  # Skip timestamps
                transcript_lines.append(line)
        
        result = ' '.join(transcript_lines)
        return result
    
    def _parse_srv(self, srv_content: str) -> str:
        """
        Parse SRV subtitle format.
        
        Args:
            srv_content: SRV subtitle content
            
        Returns:
            str: Parsed transcript text
        """
        # SRV format is typically XML-like
        # Extract text content between tags
        text_pattern = r'<text[^>]*>(.*?)</text>'
        matches = re.findall(text_pattern, srv_content, re.DOTALL)
        
        if matches:
            # Clean up HTML entities and join
            cleaned_text = []
            for match in matches:
                # Remove HTML entities
                clean_text = match.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                clean_text = clean_text.replace('&quot;', '"').replace('&#39;', "'")
                cleaned_text.append(clean_text.strip())
            
            return ' '.join(cleaned_text)
        
        return srv_content
    
    def _parse_plain_text(self, text_content: str) -> str:
        """
        Parse plain text subtitle format.
        
        Args:
            text_content: Plain text subtitle content
            
        Returns:
            str: Cleaned transcript text
        """
        # Remove common subtitle formatting
        lines = text_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip timestamp lines and empty lines
            if (line and 
                not re.match(r'^\d+$', line) and  # Skip line numbers
                not re.match(r'^\d{2}:\d{2}:\d{2}', line)):  # Skip timestamps
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)
    
    def _clean_transcript(self, transcript: str) -> str:
        """
        Clean and format the transcript text.
        
        Args:
            transcript: Raw transcript text
            
        Returns:
            str: Cleaned transcript text
        """
        # Remove extra whitespace
        transcript = re.sub(r'\s+', ' ', transcript)
        
        # Remove common subtitle artifacts
        transcript = re.sub(r'\[.*?\]', '', transcript)  # Remove [music], [applause], etc.
        transcript = re.sub(r'\(.*?\)', '', transcript)  # Remove (music), (applause), etc.
        
        # Clean up punctuation
        transcript = re.sub(r'\s+([.!?])', r'\1', transcript)  # Fix spacing before punctuation
        transcript = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', transcript)  # Add space after sentences
        
        return transcript.strip()
    
    def get_video_info(self, video_url: str) -> Optional[Dict[str, Any]]:
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
