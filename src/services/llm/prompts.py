"""
Prompt templates for the LLM service.
"""

SCORE_TRANSCRIPT_SYSTEM = (
    "You are a helpful assistant that evaluates YouTube video transcripts. "
    "Analyze for clarity, structure, informativeness, engagement, and pacing. "
    "Return a concise JSON object with numeric scores (0-100) and a short rationale."
)

SCORE_TRANSCRIPT_USER = (
    """
    You evaluate a single podcast transcript segment for VIRAL short-form potential (TikTok, YouTube Shorts, Reels).
    
    Rules:
    - Score only this segment (not the whole episode).
    - Favor surprising or contrarian claims, emotionally charged or controversial takes, unique insights, crisp story beats, quotable lines, and curiosity hooks.
    - Reward segments that would make a scroller pause in the first 3–5 seconds.
    - Penalize vague filler, meandering setup with no payoff, overly technical detail with no hook, or low-stakes chatter.
    - Keep outputs concise and strictly valid JSON.

    Output schema (STRICT JSON only):
    {{
    "overall": <number 0-100>,              // Overall viral potential score
    "clarity": <number 0-100>,             // How clear and understandable the content is
    "structure": <number 0-100>,            // How well-organized and logical the flow is
    "informativeness": <number 0-100>,     // How valuable and informative the content is
    "engagement": <number 0-100>,           // How engaging and attention-grabbing it is
    "pacing": <number 0-100>,             // How well-paced and dynamic the delivery is
    "rationale": "<<=150 chars explanation>>"  // Brief explanation of the scoring
    }}


    Transcript:\n\n{transcript}
    """
)
