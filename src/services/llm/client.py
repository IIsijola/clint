"""
LLM Client built on top of Ollama for prompting tasks.
"""

from typing import Optional, List, Dict, Any
import json
import ollama
import time
import re
from dataclasses import dataclass

from .prompts import SCORE_TRANSCRIPT_SYSTEM, SCORE_TRANSCRIPT_USER


@dataclass
class TranscriptScore:
    """
    Structured result for transcript scoring.
    """
    overall: float
    clarity: float
    structure: float
    informativeness: float
    engagement: float
    pacing: float
    rationale: str
    original_segment: str
    scoring_duration: float  # Time taken to score in seconds


@dataclass
class ViralScore:
    """
    Structured result for viral potential scoring.
    """
    score: int
    reason: str
    hookline: str
    tags: list[str]
    summary: str


@dataclass
class ScoredChunk:
    """
    A chunk of transcript with its score and metadata.
    """
    chunk_index: int
    start_char: int
    end_char: int
    text: str
    score: TranscriptScore
    overall_score: float


@dataclass
class ScoredChunksResult:
    """
    Result containing all scored chunks sorted by score.
    """
    chunks: List[ScoredChunk]
    total_chunks: int
    total_scoring_time: float
    average_score: float
    highest_score: float
    lowest_score: float


class LLMClient:
    """
    Minimal LLM client wrapper (Ollama) for common prompting tasks.
    """

    @staticmethod
    def score_transcript(transcript: str, model: str = "llama3.1:8b") -> Optional[TranscriptScore]:
        """
        Score a transcript and return a structured TranscriptScore object.

        Returns None if parsing fails or model unavailable.
        """
        if not transcript or not transcript.strip():
            return None

        start_time = time.time()
        
        messages = [
            {"role": "system", "content": SCORE_TRANSCRIPT_SYSTEM},
            {"role": "user", "content": SCORE_TRANSCRIPT_USER.format(transcript=transcript[:15000])},
        ]

        try:
            resp = ollama.chat(model=model, messages=messages)
            content = resp["message"]["content"]
            
            # Best-effort JSON extraction
            content = content.strip()
            if not content:
                print("[DEBUG] Empty response from LLM")
                return None
                
            # Attempt to locate a JSON object if there's extra text
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                content = content[start:end+1]
            else:
                return None
                
            data = json.loads(content)
            
            # Calculate duration
            end_time = time.time()
            duration = end_time - start_time
            
            # Convert to TranscriptScore dataclass
            return TranscriptScore(
                overall=float(data.get("overall", 0)),
                clarity=float(data.get("clarity", 0)),
                structure=float(data.get("structure", 0)),
                informativeness=float(data.get("informativeness", 0)),
                engagement=float(data.get("engagement", 0)),
                pacing=float(data.get("pacing", 0)),
                rationale=str(data.get("rationale", "")),
                original_segment=transcript,
                scoring_duration=duration
            )
        except Exception as e:
            print(f"Scoring transcript failed: {e}")
            return None

    @staticmethod
    def score_transcript_chunks(transcript: str, chunk_size: int = 1000, overlap: int = 100, model: str = "llama3.1:8b") -> Optional[ScoredChunksResult]:
        """
        Break a transcript into chunks, score each chunk, and return sorted results.
        
        Args:
            transcript: The full transcript text to chunk and score
            chunk_size: Maximum characters per chunk (default: 1000)
            overlap: Number of characters to overlap between chunks (default: 100)
            
        Returns:
            ScoredChunksResult: Sorted chunks with scores and statistics
        """
        if not transcript or not transcript.strip():
            return None
            
        # Break transcript into chunks
        chunks = LLMClient._create_chunks(transcript, chunk_size, overlap)
        
        if not chunks:
            return None
            
        # Score each chunk
        scored_chunks = []
        total_scoring_time = 0.0
        
        for i, (start_char, end_char, chunk_text) in enumerate(chunks):
            if not chunk_text.strip():
                continue
                
            # Score the chunk
            score = LLMClient.score_transcript(chunk_text, model)
            
            if score is None:
                continue
                
            # Create scored chunk
            scored_chunk = ScoredChunk(
                chunk_index=i,
                start_char=start_char,
                end_char=end_char,
                text=chunk_text,
                score=score,
                overall_score=score.overall
            )
            
            scored_chunks.append(scored_chunk)
            total_scoring_time += score.scoring_duration
        
        if not scored_chunks:
            return None
            
        # Sort by overall score (highest first)
        scored_chunks.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Calculate statistics
        scores = [chunk.overall_score for chunk in scored_chunks]
        average_score = sum(scores) / len(scores) if scores else 0.0
        highest_score = max(scores) if scores else 0.0
        lowest_score = min(scores) if scores else 0.0
        
        return ScoredChunksResult(
            chunks=scored_chunks,
            total_chunks=len(scored_chunks),
            total_scoring_time=total_scoring_time,
            average_score=average_score,
            highest_score=highest_score,
            lowest_score=lowest_score
        )
    
    @staticmethod
    def _create_chunks(text: str, chunk_size: int, overlap: int) -> List[tuple[int, int, str]]:
        """
        Break text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Characters to overlap between chunks
            
        Returns:
            List of (start_char, end_char, chunk_text) tuples
        """
        chunks = []
        start = 0
        
        while start < len(text):
            # Find the end position for this chunk
            end = min(start + chunk_size, len(text))
            
            # Try to break at sentence boundaries if possible
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                search_start = max(start, end - 100)
                sentence_endings = ['.', '!', '?', '\n']
                
                for i in range(end - 1, search_start - 1, -1):
                    if text[i] in sentence_endings:
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append((start, end, chunk_text))
            
            # Move start position with overlap
            start = max(start + 1, end - overlap)
            
            # Prevent infinite loop
            if start >= end:
                start = end
        
        return chunks


