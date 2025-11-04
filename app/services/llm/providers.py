# app/services/llm/providers.py
import httpx
import anthropic
import openai
import google.generativeai as genai
from typing import Dict, Any, List, Optional
import base64
from .base import LLMProvider, LLMResponse

class OpenRouterProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        super().__init__(api_key, base_url)
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    async def generate(
        self, 
        prompt: str, 
        model: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Build user message with attachments if present
        user_content = [{"type": "text", "text": prompt}]
        
        if attachments:
            for att in attachments:
                if att.get('mime_type', '').startswith('image/'):
                    # For images, include as base64
                    base64_data = base64.b64encode(att['content']).decode('ascii')
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{att['mime_type']};base64,{base64_data}"
                        }
                    })
                else:
                    # For other files, include as text in the prompt
                    content_text = att['content'].decode('utf-8', errors='replace') if isinstance(att['content'], bytes) else att['content']
                    user_content[0]["text"] += f"\n\n--- File: {att['name']} ---\n{content_text}\n--- End of {att['name']} ---"
        
        messages.append({"role": "user", "content": user_content})
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                provider="openrouter",
                usage=response.usage.model_dump() if response.usage else None
            )
        except Exception as e:
            raise Exception(f"OpenRouter API error: {str(e)}")
    
    def is_available(self) -> bool:
        return bool(self.api_key)

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key,
            base_url=base_url
        )
    
    async def generate(
        self, 
        prompt: str, 
        model: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        # Build prompt with attachments
        full_prompt = prompt
        if attachments:
            for att in attachments:
                if not att.get('mime_type', '').startswith('image/'):
                    content_text = att['content'].decode('utf-8', errors='replace') if isinstance(att['content'], bytes) else att['content']
                    full_prompt += f"\n\n--- File: {att['name']} ---\n{content_text}\n--- End of {att['name']} ---"
        
        try:
            message = await self.client.messages.create(
                model=model,
                system=system_prompt or "You are a helpful assistant.",
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            return LLMResponse(
                content=message.content[0].text if message.content else "",
                model=model,
                provider="anthropic",
                usage={"total_tokens": message.usage.input_tokens + message.usage.output_tokens}
            )
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def is_available(self) -> bool:
        return bool(self.api_key)

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    async def generate(
        self, 
        prompt: str, 
        model: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Build user message with attachments
        user_content = [{"type": "text", "text": prompt}]
        
        if attachments:
            for att in attachments:
                if att.get('mime_type', '').startswith('image/'):
                    base64_data = base64.b64encode(att['content']).decode('ascii')
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{att['mime_type']};base64,{base64_data}"
                        }
                    })
                else:
                    content_text = att['content'].decode('utf-8', errors='replace') if isinstance(att['content'], bytes) else att['content']
                    user_content[0]["text"] += f"\n\n--- File: {att['name']} ---\n{content_text}\n--- End of {att['name']} ---"
        
        messages.append({"role": "user", "content": user_content})
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                provider="openai",
                usage=response.usage.model_dump() if response.usage else None
            )
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def is_available(self) -> bool:
        return bool(self.api_key)

from openai import AsyncOpenAI

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    
    async def generate(
        self, 
        prompt: str, 
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        # Strip provider prefix if present (e.g., "google/gemini-2.0-flash" -> "gemini-2.0-flash")
        actual_model = model.split('/', 1)[-1] if '/' in model else model
        
        # Build prompt with attachments
        full_prompt = prompt
        if attachments:
            for att in attachments:
                if not att.get('mime_type', '').startswith('image/'):
                    content_text = att['content'].decode('utf-8', errors='replace') if isinstance(att['content'], bytes) else att['content']
                    full_prompt += f"\n\n--- File: {att['name']} ---\n{content_text}\n--- End of {att['name']} ---"
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": full_prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=actual_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                provider="gemini",
                usage={
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            )
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def is_available(self) -> bool:
        return bool(self.api_key)