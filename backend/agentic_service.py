import json
import requests
import re
from typing import Dict, Any, Optional, List, Tuple
from collections import deque
from datetime import datetime

class AgenticMemory:
    """Memory system for exactly 10 messages + PDF context"""
    
    def __init__(self):
        self.messages = deque(maxlen=10)  # Exactly 10 messages as requested
        self.pdf_context = []  # Track uploaded PDFs
        self.current_topic = None
    
    def add_message(self, role: str, content: str, metadata: dict = None):
        """Add message to memory"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
    
    def add_pdf_context(self, filename: str):
        """Track PDF uploads"""
        if len(self.pdf_context) >= 2:
            self.pdf_context.pop(0)  # Keep max 2 PDFs
        if filename not in self.pdf_context:
            self.pdf_context.append(filename)
    
    def get_context_summary(self) -> str:
        """Get formatted context for AI"""
        context_parts = []
        
        if self.pdf_context:
            context_parts.append(f"📄 Available PDFs: {', '.join(self.pdf_context)}")
        
        if self.current_topic:
            context_parts.append(f"🎯 Current topic: {self.current_topic}")
        
        if self.messages:
            context_parts.append("💬 Recent conversation:")
            for msg in list(self.messages)[-5:]:  # Last 5 messages
                content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                context_parts.append(f"{msg['role']}: {content_preview}")
        
        return "\n".join(context_parts) if context_parts else "No conversation history"
    
    def get_recent_messages(self) -> list:
        """Get recent messages"""
        return list(self.messages)
    
    def clear_messages(self):
        """Clear conversation messages but keep PDF context"""
        self.messages.clear()
    
    def update_topic(self, topic: str):
        """Update current conversation topic"""
        self.current_topic = topic

class AgenticService:
    def __init__(self, ai_agent_url: str, secret_key: str):
        self.ai_agent_url = ai_agent_url
        self.secret_key = secret_key
        self.headers = {"Content-Type": "application/json"}
        self.memory = AgenticMemory()
        
        print(f"[AgenticService] Using endpoint: {self.ai_agent_url}")
        print(f"[AgenticService] Using API key: {self.secret_key}")

    def _make_request(self, prompt: str) -> str:
        """Send request to the Intelligize AI API"""
        try:
            payload = {
                "Prompt": prompt,
                "responseMaxTokens": 4000,
                "intelligizeAIAccountType": 2,
                "endpointSecretKey": self.secret_key,
                "Source": "Backend - Dev - PBD",
                "Category": "Agentic Routing",
                "AppKey": "PBD",
                "LLMMetadata": True
            }

            response = requests.post(self.ai_agent_url, headers=self.headers, json=payload, timeout=30)
            
            if not response.text.strip():
                return "Error: Empty response from AI API"

            try:
                data = response.json()
                return data['content'][0]['text']
            except Exception:
                return f"Error: Non-JSON response: {response.text}"

        except Exception as e:
            return f"Error: {str(e)}"

    def _check_greeting(self, query: str) -> Optional[Dict]:
        """FIXED - Enhanced greeting detection with comprehensive debugging"""
        query_lower = query.lower().strip()
        
        print(f"[GREETING DEBUG] Input query: '{query}'")
        print(f"[GREETING DEBUG] Lowercase query: '{query_lower}'")
        
        # Comprehensive greeting patterns
        greeting_patterns = {
            "hello": ["hi", "hello", "hey", "hiya", "good morning", "good afternoon", "good evening", "hi there", "hello there"],
            "goodbye": ["goodbye", "bye", "see you", "farewell", "good night", "bye bye", "see ya"],
            "how_are_you": ["how are you", "how r u", "how do you do", "what's up", "how's it going", "how are things"]
        }
        
        print(f"[GREETING DEBUG] Checking patterns...")
        
        # Check each pattern with detailed logging
        greeting_type = None
        matched_pattern = None
        
        for pattern_type, patterns in greeting_patterns.items():
            print(f"[GREETING DEBUG] Checking {pattern_type} patterns: {patterns}")
            for pattern in patterns:
                if pattern in query_lower:
                    greeting_type = pattern_type
                    matched_pattern = pattern
                    print(f"[GREETING DEBUG] ✅ MATCH FOUND! Pattern: '{pattern}' Type: {pattern_type}")
                    break
            if greeting_type:
                break
        
        if not greeting_type:
            print(f"[GREETING DEBUG] ❌ No greeting pattern matched for: '{query_lower}'")
            return None
        
        print(f"[GREETING DEBUG] Processing greeting type: {greeting_type}")
        
        # Generate appropriate response - FIXED goodbye to not end session
        if greeting_type == "goodbye":
            response = "Goodbye for now! 👋\n\nI'm still here whenever you need help with:\n📝 **Summarization** - Text or PDF documents\n📊 **Comparison** - Text or PDF analysis\n❓ **PDF Q&A** - Document questions\n\nFeel free to continue our conversation anytime!"
            topic = "Temporary Farewell"
            
        elif greeting_type == "how_are_you":
            response = "I'm functioning perfectly and ready to help! 🤖\n\nI specialize in:\n📝 **Summarization** - Summarize text or PDF documents\n📊 **Comparison** - Compare two texts or PDFs\n❓ **PDF Q&A** - Answer questions about uploaded PDFs\n\nWhat would you like me to help you with today?"
            topic = "Status Inquiry"
            
        else:  # hello type (including "hi")
            response = "Hello! 👋 I'm your intelligent AI assistant powered by Claude 3 Haiku.\n\nI can help you with:\n📝 **Summarization** - Summarize text or PDF documents\n📊 **Comparison** - Compare two texts or PDF documents\n❓ **PDF Q&A** - Ask questions about uploaded PDFs\n\n🚫 I politely decline requests outside these areas.\n\nHow can I assist you today?"
            topic = "Greeting"
        
        # Update memory
        self.memory.update_topic(topic)
        self.memory.add_message("assistant", response, {"task_type": "greeting", "matched_pattern": matched_pattern})
        
        print(f"[GREETING DEBUG] ✅ Generated response for {greeting_type}: {response[:50]}...")
        
        return {
            "category": "greeting",
            "confidence": 0.95,
            "reasoning": f"Detected {greeting_type} greeting pattern: '{matched_pattern}'",
            "response": response,
            "parameters": {
                "greeting_type": greeting_type,
                "matched_pattern": matched_pattern
            }
        }

    def _check_scope(self, query: str) -> Optional[Dict]:
        """Check if query is out of scope"""
        out_of_scope_indicators = [
            "write", "poem", "story", "joke", "weather", "news", "calculate", "math", 
            "translate", "code", "programming", "recipe", "game", "play", "sing", "draw",
            "create", "generate", "compose", "paint", "dance", "music", "movie", "book"
        ]
        
        query_lower = query.lower()
        
        # Allow our core tasks
        allowed_tasks = ["summarize", "compare", "question", "what", "how", "why", "explain", "analyze", "upload", "pdf"]
        if any(task in query_lower for task in allowed_tasks):
            return None
        
        # Check for out-of-scope requests
        if any(indicator in query_lower for indicator in out_of_scope_indicators):
            response = """🚫 I can only help with these specific tasks:

📝 **Summarization** - Summarize text or PDF documents
📊 **Comparison** - Compare two texts or PDF documents  
❓ **PDF Q&A** - Answer questions about uploaded PDFs

Your request appears to be outside my scope. Please ask me to:
- Summarize some text or a PDF
- Compare two texts or documents
- Answer questions about an uploaded PDF

How can I help you with one of these tasks?"""
            
            # Add response to memory
            self.memory.add_message("assistant", response, {"task_type": "out_of_scope"})
            self.memory.update_topic("Out of Scope Request")
            
            return {
                "category": "out_of_scope",
                "confidence": 0.9,
                "reasoning": "Request is outside allowed scope",
                "response": response,
                "parameters": {}
            }
        
        return None

    def classify_with_enhanced_routing(self, user_query: str, context_info: str = None) -> Dict:
        """FIXED - Enhanced classification with priority greeting detection"""
        
        print(f"[Classification] Processing query: '{user_query}'")
        
        # Add user query to memory first
        self.memory.add_message("user", user_query)
        
        # PRIORITY 1: Check for greetings FIRST - FIXED
        greeting_result = self._check_greeting(user_query)
        if greeting_result:
            print(f"[Classification] ✅ GREETING DETECTED: {greeting_result['parameters']['greeting_type']}")
            return greeting_result
        else:
            print(f"[Classification] No greeting detected in: '{user_query}'")
        
        # PRIORITY 2: Check for out-of-scope requests
        scope_result = self._check_scope(user_query)
        if scope_result:
            print(f"[Classification] ✅ OUT-OF-SCOPE DETECTED")
            return scope_result
        
        # PRIORITY 3: Use existing classification logic
        print(f"[Classification] Proceeding with general classification...")
        return self.classify_and_route(user_query, context_info)

    def classify_and_route(self, user_query: str, context_info: str = None) -> Dict:
        """Enhanced classification with memory integration"""
        classification_prompt = f"""
You are an intelligent AI assistant with exactly these capabilities:

ALLOWED TASKS:
1. summarization - condensing given text or uploaded PDFs into summaries
2. comparison - comparing two pieces of text or two PDFs
3. rag - answering questions about uploaded PDFs using retrieval

Anything else should be classified as "general".

MEMORY CONTEXT: {self.memory.get_context_summary()}

USER QUERY: "{user_query}"

ADDITIONAL CONTEXT: {context_info or "No additional context"}

Respond ONLY with valid JSON:
{{
    "category": "summarization|comparison|rag|general",
    "confidence": 0.0,
    "reasoning": "Your reasoning",
    "parameters": {{
        "text1": "",
        "text2": "",
        "query": "",
        "summary_type": "brief|detailed|bullet_points|micro|audience",
        "comparison_type": "comprehensive|similarities|differences"
    }}
}}
""".strip()

        resp = self._make_request(classification_prompt)
        
        try:
            if not resp or resp.startswith("Error:"):
                raise ValueError(resp)

            parsed = json.loads(resp.strip())
            
            if "category" not in parsed:
                raise ValueError("Missing 'category' in output")
            
            # Update memory topic based on classification
            category = parsed.get("category", "general")
            if category == "summarization":
                self.memory.update_topic("Text/PDF Summarization")
            elif category == "comparison":
                self.memory.update_topic("Text/PDF Comparison")
            elif category == "rag":
                self.memory.update_topic("PDF Question & Answer")
            else:
                self.memory.update_topic("General Inquiry")
            
            return parsed

        except Exception as e:
            print(f"[AgenticService] Classification error: {e}")
            return {
                "category": "general",
                "confidence": 0.0,
                "reasoning": f"Fallback after classification error: {e}",
                "parameters": {"query": user_query}
            }

    def extract_two_texts_from_query(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract two texts for comparison from query"""
        # Method 1: "Text 1:" and "Text 2:" format
        pattern1 = r'text\s*1\s*[:]\s*(.*?)\s*text\s*2\s*[:]\s*(.*?)(?:\n|$)'
        match1 = re.search(pattern1, query, re.IGNORECASE | re.DOTALL)
        if match1:
            return match1.group(1).strip(), match1.group(2).strip()
        
        # Method 2: Quoted texts with vs
        pattern2 = r'"([^"]+)"\s*(?:vs|versus|and)\s*"([^"]+)"'
        match2 = re.search(pattern2, query, re.IGNORECASE)
        if match2:
            return match2.group(1).strip(), match2.group(2).strip()
        
        # Method 3: Separator-based splitting
        separators = ['\n---\n', '\n\n---\n\n', '\nvs\n', '\nversus\n', '\n\n\n', '\n\n']
        for sep in separators:
            if sep in query:
                parts = query.split(sep, 1)
                if len(parts) == 2:
                    text1 = parts[0].strip()
                    text2 = parts[1].strip()
                    
                    # Remove common prefixes
                    prefixes = ['text 1:', 'text1:', 'first:', 'document 1:', 'compare', 'text 2:', 'text2:', 'second:', 'document 2:']
                    for prefix in prefixes:
                        if text1.lower().startswith(prefix):
                            text1 = text1[len(prefix):].strip()
                        if text2.lower().startswith(prefix):
                            text2 = text2[len(prefix):].strip()
                    
                    if len(text1) > 20 and len(text2) > 20:
                        return text1, text2
        
        return None, None

    def extract_text_for_summary(self, query: str) -> Optional[str]:
        """Extract text for summarization from query"""
        keywords = ["summarize", "summary", "sum up", "brief", "overview", "gist", "please", "this", "the following"]
        
        text = query
        for keyword in keywords:
            text = re.sub(rf'\b{keyword}\b', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\s+', ' ', text.strip())
        
        if len(text) > 50:
            return text
        
        return None

    def add_response_to_memory(self, response: str, task_type: str):
        """Add AI response to memory"""
        self.memory.add_message("assistant", response, {"task_type": task_type})

    def get_memory_info(self) -> Dict:
        """Get current memory state"""
        return {
            "message_count": len(self.memory.messages),
            "available_pdfs": self.memory.pdf_context,
            "current_topic": self.memory.current_topic,
            "recent_messages": self.memory.get_recent_messages()
        }

    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear_messages()
        self.memory.current_topic = None

    def process_query(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process query with enhanced routing"""
        classification = self.classify_with_enhanced_routing(user_query, str(context) if context else None)
        
        return {
            "success": True,
            "classification": classification,
            "original_query": user_query,
            "memory_info": self.get_memory_info()
        }
