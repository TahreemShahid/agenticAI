import requests
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def call_ai_agent(ai_agent_url: str, prompt: str, secret_key: str) -> str:
    """Call the AI agent for summarization"""
    payload = {
        "Prompt": prompt,
        "responseMaxTokens": 4000,
        "intelligizeAIAccountType": 2,
        "endpointSecretKey": secret_key,
        "Source": "Backend - Dev - PBD",
        "Category": "Summarization",
        "AppKey": "PBD",
        "LLMMetadata": True,
    }
    try:
        logger.info(f"Calling AI agent for summarization at: {ai_agent_url}")
        response = requests.post(ai_agent_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["content"][0]["text"]
    except Exception as e:
        logger.error(f"Error in AI summarization call: {e}")
        return f"ERROR in AI call: {e}"


def build_prompt(
    text: str, summary_type: str = "brief", audience: Optional[str] = None
) -> str:
    """Build the summarization prompt based on type and audience"""
    if summary_type == "detailed":
        return f"Summarize the following text in a detailed, clear paragraph of 150–200 words:\n\n{text}"
    elif summary_type == "bullet_points":
        return f"Summarize the following text into exactly 10 bullet points. Cover all major ideas and facts:\n\n{text}"
    elif summary_type == "micro":
        return f"Summarize this text in under 75 words. Focus only on the essentials:\n\n{text}"
    elif summary_type == "audience" and audience == "general":
        return f"Summarize this disclosure for a general audience such as investors or journalists. Use plain English, focus on functions and practices:\n\n{text}"
    elif summary_type == "audience" and audience == "professional":
        return f"Summarize this disclosure for a finance professional. Use appropriate financial terminology:\n\n{text}"
    else:
        # Default to a brief summary
        return f"Summarize the following text in a concise paragraph:\n\n{text}"


def summarize(
    text: str,
    ai_agent_url: str,
    secret_key: str,
    summary_type: str = "brief",
    audience: Optional[str] = None,
) -> str:
    """Summarize text using AI agent"""
    if not text.strip():
        return "Error: No text provided for summarization."

    logger.info(
        f"Starting summarization with type: {summary_type}, audience: {audience}"
    )

    prompt = build_prompt(text, summary_type=summary_type, audience=audience)
    return call_ai_agent(ai_agent_url, prompt, secret_key)


def generate_mock_summary(
    text: str, summary_type: str = "brief", audience: Optional[str] = None
) -> str:
    """Generate a mock summary for testing purposes"""
    word_count = len(text.split())
    char_count = len(text)

    if summary_type == "detailed":
        return f"""DETAILED SUMMARY (Mock Response):

This text contains approximately {word_count} words and {char_count} characters. The content appears to cover various topics and themes that would be analyzed in detail in a real AI-powered summary.

Key aspects that would be highlighted in a detailed analysis include:
- Main themes and concepts
- Important facts and figures
- Structural organization
- Key conclusions or findings

This mock summary demonstrates the detailed analysis format that would be provided by the AI service when properly configured.

Note: This is a mock response. Connect your AI service for detailed summarization."""

    elif summary_type == "bullet_points":
        return f"""BULLET POINT SUMMARY (Mock Response):

• Text contains {word_count} words with {char_count} characters
• Content covers multiple topics and themes
• Structure includes various sections and subsections
• Key information is distributed throughout the text
• Main ideas are presented in logical sequence
• Supporting details provide context and examples
• Conclusions or findings are included
• Professional terminology is used appropriately
• Content is suitable for {audience or 'general'} audience
• Summary format demonstrates bullet point structure

Note: This is a mock response. Connect your AI service for detailed bullet point summarization."""

    elif summary_type == "micro":
        return f"""MICRO SUMMARY (Mock Response):

This {word_count}-word text covers key topics and themes. Main points include essential information and conclusions. Content is structured for clarity and comprehension.

Note: This is a mock response. Connect your AI service for micro summarization."""

    elif summary_type == "audience":
        audience_text = "general" if audience == "general" else "professional"
        return f"""AUDIENCE-SPECIFIC SUMMARY (Mock Response):

This {word_count}-word text has been analyzed for a {audience_text} audience. The content includes relevant information and terminology appropriate for this target demographic. Key points are presented in an accessible format suitable for {audience_text} readers.

Note: This is a mock response. Connect your AI service for audience-specific summarization."""

    else:  # brief
        return f"""BRIEF SUMMARY (Mock Response):

This text contains {word_count} words and covers various topics and themes. The content is well-structured and includes key information that would be highlighted in a proper AI-generated summary. Main points and conclusions are presented clearly.

Note: This is a mock response. Connect your AI service for brief summarization."""
