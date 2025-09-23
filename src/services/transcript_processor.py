"""
Transcript processing service - handles YouTube transcript extraction and segmentation
"""

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


@dataclass
class TranscriptLine:
    """
    A single caption line with timing information.
    """
    text: str
    start: float
    end: Optional[float] = None


@dataclass
class TranscriptSegment:
    """
    Group of caption lines within a fixed time window.
    """
    index: int
    start: float
    end: float
    lines: List[TranscriptLine]


@dataclass
class TranscriptWithSegmentsResult:
    """
    Combined result: plain transcript plus 60s segments with timestamps.
    """
    transcript_result: TranscriptResult
    segments: List[TranscriptSegment]


class TranscriptProcessor:
    """
    Service for processing YouTube transcripts and creating time-based segments.
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
        start_time = time.time()
        
        try:
            # Configure yt-dlp options for transcript extraction
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en', 'en-US', 'en-GB'],  # Try English variants first
                'skip_download': True,  # We only want the transcript, not the video
                'quiet': True,
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
                    elapsed_time = time.time() - start_time
                    return TranscriptResult(
                        transcript="",
                        duration=elapsed_time,
                        success=False,
                        error_message="No subtitles or captions found for this video"
                    )
                
                # Try to find English subtitles
                transcript_text = TranscriptProcessor._extract_transcript_text(all_subtitles, ydl)
                
                if transcript_text:
                    print(f"[DEBUG] Extracted transcript length: {len(transcript_text)} characters")
                    cleaned_transcript = TranscriptProcessor._clean_transcript(transcript_text)
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

    @staticmethod
    def get_transcript_segments(video_url: str, segment_seconds: int = 60) -> List[TranscriptSegment]:
        """
        Extract timed transcript and group it into fixed-size segments.

        Each segment contains the lines (text + timestamp) that start within the
        segment time window. For example, a 4-minute video and 60-second windows
        will yield 4 segments.

        Args:
            video_url: YouTube video URL or ID
            segment_seconds: Segment duration in seconds (default: 60)

        Returns:
            List[TranscriptSegment]: Ordered segments with timed lines.
        """
        if segment_seconds <= 0:
            raise ValueError("segment_seconds must be > 0")

        # Configure yt-dlp options to fetch subtitles without downloading media
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en', 'en-US', 'en-GB'],
            'skip_download': True,
            'quiet': True,
            'no_warnings': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            duration: Optional[float] = info.get('duration')

            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            all_subtitles = {**subtitles, **automatic_captions}

            if not all_subtitles:
                return []

            lines: List[TranscriptLine] = TranscriptProcessor._extract_timed_captions(all_subtitles, ydl)
            if not lines:
                return []

            # If video duration is unknown, infer from last line end or start
            if duration is None:
                last_end_candidates: List[float] = [ln.end for ln in lines if ln.end is not None]
                if last_end_candidates:
                    duration = max(last_end_candidates)
                else:
                    duration = max((ln.start for ln in lines), default=0.0)

            # Build segments
            num_segments = int((duration + segment_seconds - 1) // segment_seconds)
            segments: List[TranscriptSegment] = []
            for idx in range(num_segments):
                seg_start = idx * segment_seconds
                seg_end = min((idx + 1) * segment_seconds, duration)
                seg_lines = [
                    ln for ln in lines
                    if ln.start >= seg_start and ln.start < seg_end
                ]
                segments.append(TranscriptSegment(index=idx, start=seg_start, end=seg_end, lines=seg_lines))

            return segments

    @staticmethod
    def get_transcript_with_segments(video_url: str, segment_seconds: int = 60) -> TranscriptWithSegmentsResult:
        """
        Convenience method that returns both the cleaned transcript text and
        time-bucketed segments (default 60s) in a single call.

        This reuses the existing transcript logic and the timed-segmentation logic
        without duplicating extraction work in callers.
        """
        transcript_result = TranscriptProcessor.get_transcript(video_url)
        # Even if transcript failed, we still attempt timed segments to provide
        # best-effort structure (may also fail gracefully and return []).
        segments = TranscriptProcessor.get_transcript_segments(video_url, segment_seconds=segment_seconds)
        return TranscriptWithSegmentsResult(
            transcript_result=transcript_result,
            segments=segments,
        )

    @staticmethod
    def _extract_transcript_text(subtitles: Dict[str, Any], ydl) -> Optional[str]:
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
                                parsed = TranscriptProcessor._parse_vtt(transcript)
                                if parsed:
                                    print(f"[DEBUG] VTT parsing successful, length: {len(parsed)}")
                                    return parsed
                            elif 'srv' in sub_format.get('ext', '').lower():
                                parsed = TranscriptProcessor._parse_srv(transcript)
                                if parsed:
                                    print(f"[DEBUG] SRV parsing successful, length: {len(parsed)}")
                                    return parsed
                            elif 'json' in sub_format.get('ext', '').lower():
                                parsed = TranscriptProcessor._parse_json3(transcript)
                                if parsed:
                                    print(f"[DEBUG] JSON3 parsing successful, length: {len(parsed)}")
                                    return parsed
                            else:
                                # Try to parse as plain text
                                parsed = TranscriptProcessor._parse_plain_text(transcript)
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
                            parsed = TranscriptProcessor._parse_vtt(transcript)
                            if parsed:
                                return parsed
                        elif 'srv' in sub_format.get('ext', '').lower():
                            parsed = TranscriptProcessor._parse_srv(transcript)
                            if parsed:
                                return parsed
                        else:
                            parsed = TranscriptProcessor._parse_plain_text(transcript)
                            if parsed:
                                return parsed
                                
                    except Exception as e:
                        print(f"[DEBUG] Parsing transcript failed: {e}")
                        continue
        
        return None

    @staticmethod
    def _extract_timed_captions(subtitles: Dict[str, Any], ydl) -> List[TranscriptLine]:
        """
        Extract caption lines with timing information from available subtitle formats.

        Tries English variants first, then falls back to any language.
        """
        def try_langs(langs: List[str]) -> List[TranscriptLine]:
            for lang in langs:
                if lang in subtitles and subtitles[lang]:
                    lines = TranscriptProcessor._parse_timed_from_formats(subtitles[lang], ydl)
                    if lines:
                        return lines
            return []

        # Prefer English
        lines = try_langs(['en', 'en-US', 'en-GB', 'en-CA', 'en-AU'])
        if lines:
            return lines

        # Fallback to any available language
        for lang, formats in subtitles.items():
            if not formats:
                continue
            lines = TranscriptProcessor._parse_timed_from_formats(formats, ydl)
            if lines:
                return lines
        return []

    @staticmethod
    def _parse_timed_from_formats(formats: List[Dict[str, Any]], ydl) -> List[TranscriptLine]:
        lines: List[TranscriptLine] = []
        for sub_format in formats:
            try:
                subtitle_url = sub_format['url']
                content = ydl.urlopen(subtitle_url).read().decode('utf-8')
                ext = sub_format.get('ext', '').lower()

                if 'json' in ext:
                    lines = TranscriptProcessor._parse_timed_json3(content)
                elif 'vtt' in ext:
                    lines = TranscriptProcessor._parse_timed_vtt(content)
                elif 'srv' in ext or 'xml' in ext:
                    lines = TranscriptProcessor._parse_timed_srv(content)
                else:
                    # Plain text has no timing information
                    lines = []

                if lines:
                    return lines
            except Exception:
                continue
        return []

    @staticmethod
    def _parse_timed_json3(json_content: str) -> List[TranscriptLine]:
        import json
        results: List[TranscriptLine] = []
        try:
            data = json.loads(json_content)
            if 'events' not in data:
                return results
            for event in data['events']:
                if 'segs' not in event:
                    continue
                text_parts: List[str] = []
                for seg in event['segs']:
                    if 'utf8' in seg:
                        text_parts.append(seg['utf8'])
                if not text_parts:
                    continue
                text = ' '.join(text_parts).strip()
                start_ms = event.get('tStartMs')
                dur_ms = event.get('dDurationMs')
                start = float(start_ms) / 1000.0 if start_ms is not None else 0.0
                end = (start + float(dur_ms) / 1000.0) if dur_ms is not None else None
                results.append(TranscriptLine(text=text, start=start, end=end))
        except Exception:
            return results
        return results

    @staticmethod
    def _parse_timed_vtt(vtt_content: str) -> List[TranscriptLine]:
        results: List[TranscriptLine] = []
        # Blocks like: 00:00:01.000 --> 00:00:03.000
        # followed by one or more text lines until a blank line
        pattern = re.compile(r"(?m)^(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*$")
        lines = vtt_content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            match = pattern.match(line)
            if match:
                sh, sm, ss, sms, eh, em, es, ems = match.groups()
                start = int(sh) * 3600 + int(sm) * 60 + int(ss) + int(sms) / 1000.0
                end = int(eh) * 3600 + int(em) * 60 + int(es) + int(ems) / 1000.0
                i += 1
                text_parts: List[str] = []
                while i < len(lines) and lines[i].strip() != "":
                    # Skip metadata lines that look like settings
                    if '-->' not in lines[i]:
                        text_parts.append(lines[i].strip())
                    i += 1
                text = ' '.join(text_parts).strip()
                if text:
                    results.append(TranscriptLine(text=text, start=start, end=end))
            else:
                i += 1
        return results

    @staticmethod
    def _parse_timed_srv(srv_content: str) -> List[TranscriptLine]:
        # Typical <text start="12.34" dur="3.21">Hello</text>
        results: List[TranscriptLine] = []
        pattern = re.compile(r"<text[^>]*start=\"([0-9]+(?:\.[0-9]+)?)\"[^>]*dur=\"([0-9]+(?:\.[0-9]+)?)\"[^>]*>(.*?)</text>", re.DOTALL)
        for start_str, dur_str, inner in re.findall(pattern, srv_content):
            try:
                start = float(start_str)
                dur = float(dur_str)
                end = start + dur
                # Basic entity cleanup
                text = inner.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                text = text.replace('&quot;', '"').replace('&#39;', "'").strip()
                if text:
                    results.append(TranscriptLine(text=text, start=start, end=end))
            except Exception:
                continue
        return results

    @staticmethod
    def _parse_json3(json_content: str) -> str:
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
    
    @staticmethod
    def _parse_vtt(vtt_content: str) -> str:
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
    
    @staticmethod
    def _parse_srv(srv_content: str) -> str:
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
    
    @staticmethod
    def _parse_plain_text(text_content: str) -> str:
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
    
    @staticmethod
    def _clean_transcript(transcript: str) -> str:
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
