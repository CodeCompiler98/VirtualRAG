import requests
import json
from typing import AsyncGenerator, Dict, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS


class LLMHandler:
    """
    Handles communication with Ollama LLM
    """
    
    def __init__(self):
        """Initialize LLM handler with configuration"""
        self.base_url = LLM_BASE_URL
        self.model = LLM_MODEL
        self.temperature = LLM_TEMPERATURE
        self.max_tokens = LLM_MAX_TOKENS
        
    def is_available(self):
        """
        Check if Ollama server is available returning true if server is responding or false otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"LLM server not available: {e}")
            return False
    
    async def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_message: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a response in real time from LLM given a prompt, context and a system message
        """
        # Build the full prompt
        full_prompt = self._build_prompt(prompt, context, system_message)
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        try:
            # Stream response from Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                yield f"Error: LLM returned status {response.status_code}"
                return
            
            # Parse and yield chunks
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            yield f"Error generating response: {str(e)}"
    
    def _build_prompt(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_message: Optional[str] = None
    ):
        """
        Build the complete prompt adding on context and system message
        """
        parts = []
        
        # Add system message if provided
        if system_message:
            parts.append(f"System: {system_message}\n")
        
        # Add context if provided
        if context:
            parts.append(f"Context from documents:\n{context}\n")
        
        # Add user query
        parts.append(f"User question: {prompt}\n")
        parts.append("Assistant response:")
        
        return "\n".join(parts)
