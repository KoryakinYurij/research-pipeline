"""Call Gemma 4 31B via Google AI Studio API for cross-summary generation.

Implemented in T4 (Prototype).
Key design decisions from T1:
- SDK: google-genai (google-generativeai is deprecated)
- Auth: GOOGLE_API_KEY env var
- Model ID: gemma-4-31B-it
- Context: 256K tokens — enough for two reports + summary, no chunking needed
"""

async def generate_cross_summary(kilo_output: str, opencode_output: str) -> str:
    """Send two agent outputs to Gemma 4 31B, return structured cross-summary in Russian.

    Returns: Markdown-formatted comparison with sections:
    (1) what's in common, (2) differences, (3) items to verify.
    """
    raise NotImplementedError("T4")
