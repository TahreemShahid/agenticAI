# Text comparison service for FastAPI
import requests
import json
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_comparison_prompt(text1: str, text2: str, comparison_type: str = "comprehensive") -> str:
    """Build the comparison prompt based on the texts and comparison type."""
    
    type_instructions = {
        "similarities": "Focus primarily on identifying and analyzing similarities between the two texts.",
        "differences": "Focus primarily on identifying and analyzing differences between the two texts.", 
        "comprehensive": "Provide a comprehensive analysis including both similarities and differences."
    }
    
    instruction = type_instructions.get(comparison_type, type_instructions["comprehensive"])
    
    prompt_text = f'''
    ROLE:
    You are an expert comparative analyst trained in high-accuracy textual analysis.
    
    TASK:
    {instruction}
    
    INSTRUCTIONS:
    1. Analyze both texts carefully
    2. Provide structured comparison results
    3. Include specific examples and evidence
    4. Be objective and thorough
    5. Format your response as clear, readable text and do not add any lines , just give the analysis.
    
    TEXT 1:
    {text1}
    
    TEXT 2:
    {text2}
    
    Please provide a detailed comparison analysis.
    '''
    
    return prompt_text

def call_ai_agent(ai_agent_url: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Call the external AI agent API."""
    try:
        logger.info(f"Calling AI agent at: {ai_agent_url}")
        response = requests.post(ai_agent_url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"AI API call failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in AI API call: {e}")
        return None

def extract_comparison_output(ai_response_text: str) -> str:
    """Extract and clean the comparison output from AI response."""
    try:
        # Try to find JSON block first
        json_start = ai_response_text.find('{')
        json_end = ai_response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_block = ai_response_text[json_start:json_end]
            parsed = json.loads(json_block)
            # If it's a dict, extract the relevant content
            if isinstance(parsed, dict):
                return parsed.get('content', ai_response_text)
        
        # If no JSON found or parsing failed, return the raw text
        return ai_response_text
    except Exception as ex:
        logger.warning(f"Parsing error: {ex}")
        return ai_response_text

def compare_texts(text1: str, text2: str, comparison_type: str = "comprehensive", 
                 ai_agent_url: str = None, secret_key: str = None) -> str:
    """Compare two texts using AI agent or return mock response."""
    
    logger.info(f"Starting text comparison with type: {comparison_type}")
    
    # Validate inputs
    if not text1.strip() or not text2.strip():
        return "Error: Both texts must contain content for comparison."
    
    # If no AI agent URL or secret key provided, return a mock response
    if not ai_agent_url or not secret_key:
        logger.info("No AI service configured, using mock comparison")
        return generate_mock_comparison(text1, text2, comparison_type)
    
    try:
        prompt = build_comparison_prompt(text1, text2, comparison_type)
        payload = {
            "Prompt": prompt,
            "responseMaxTokens": 4000,
            "intelligizeAIAccountType": 2,
            "endpointSecretKey": secret_key,
            "Source": "Backend - Dev - PBD",
            "Category": "Text Comparison",
            "AppKey": "PBD",
            "LLMMetadata": True
        }
        
        response = call_ai_agent(ai_agent_url, payload)
        if not response:
            logger.warning("AI service call failed, falling back to mock response")
            return generate_mock_comparison(text1, text2, comparison_type)
        
        ai_response_text = response.get('content', [{}])[0].get('text', 'No response content')
        comparison_output = extract_comparison_output(ai_response_text)
        
        if not comparison_output.strip():
            logger.warning("Empty AI response, falling back to mock response")
            return generate_mock_comparison(text1, text2, comparison_type)
            
        return comparison_output
        
    except Exception as e:
        logger.error(f"Error in comparison service: {e}")
        return f"Error occurred during comparison: {str(e)}. Falling back to basic analysis."

def generate_mock_comparison(text1: str, text2: str, comparison_type: str) -> str:
    """Generate a mock comparison for testing purposes."""
    
    word_count1 = len(text1.split())
    word_count2 = len(text2.split())
    char_count1 = len(text1)
    char_count2 = len(text2)
    
    # Basic text analysis
    sentences1 = text1.count('.') + text1.count('!') + text1.count('?')
    sentences2 = text2.count('.') + text2.count('!') + text2.count('?')
    
    if comparison_type == "similarities":
        return f"""SIMILARITIES ANALYSIS:

 **Text Structure & Format**
- Both texts contain {min(word_count1, word_count2)} or more words
- Both follow similar paragraph structures
- Common themes and topics may be present

 **Linguistic Patterns**
- Similar sentence structures observed
- Common vocabulary and terminology usage
- Comparable tone and writing style

 **Content Overlap**
- Shared concepts and ideas identified
- Similar approaches to topic presentation
- Overlapping subject matter areas

Note: This is a mock analysis. Connect your AI service for detailed comparison."""
        
    elif comparison_type == "differences":
        return f"""DIFFERENCES ANALYSIS:

 **Text Length & Structure**
- Text A: {word_count1} words, {char_count1} characters, ~{sentences1} sentences
- Text B: {word_count2} words, {char_count2} characters, ~{sentences2} sentences
- Length difference: {abs(word_count1 - word_count2)} words

 **Style & Tone Variations**
- Different writing approaches detected
- Varying levels of formality
- Distinct presentation methods

 **Content Distinctions**
- Unique topics and themes in each text
- Different perspectives on similar subjects
- Varying depth and detail levels

 **Specific Differences**
- Text A focuses on different aspects
- Text B emphasizes alternative viewpoints
- Contrasting conclusions or recommendations

Note: This is a mock analysis. Connect your AI service for detailed comparison."""

    else:  # comprehensive
        return f"""COMPREHENSIVE TEXT COMPARISON ANALYSIS:

##  OVERVIEW
- Text A: {word_count1} words, {char_count1} characters, ~{sentences1} sentences
- Text B: {word_count2} words, {char_count2} characters, ~{sentences2} sentences
- Analysis Type: Comprehensive Comparison

##  SIMILARITIES
**Structural Elements**
- Both texts maintain organized paragraph structure
- Similar approaches to topic introduction
- Comparable use of examples and evidence

 **Content Themes**
- Shared subject matter areas
- Common terminology and concepts
- Similar target audience considerations

##  DIFFERENCES  
 **Length & Scope**
- Significant difference in word count ({abs(word_count1 - word_count2)} words)
- Varying levels of detail and elaboration
- Different coverage breadth

 **Style & Approach**
- Distinct writing styles and tones
- Different organizational patterns
- Varying use of supporting evidence

##  KEY INSIGHTS
- The texts share fundamental themes but differ in execution
- Each text brings unique perspectives to common topics  
- Style and presentation methods vary significantly
- Both texts serve their intended purposes effectively

##  RECOMMENDATIONS
- Consider combining strengths from both texts
- Text A's approach works well for [specific context]
- Text B's style is more suitable for [different context]

Note: This is a mock analysis. Connect your AI service for detailed, accurate comparison."""