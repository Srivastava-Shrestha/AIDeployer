# app/services/llm/manager.py
from typing import Dict, List, Optional, Any
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import LLMProvider, LLMResponse
from .providers import OpenRouterProvider, AnthropicProvider, OpenAIProvider, GeminiProvider
from app.config import settings

logger = logging.getLogger(__name__)

class LLMManager:
    def __init__(self):
        self.providers = self._initialize_providers()
        self.model_mapping = {
            "anthropic/claude-opus-4.1": ["openrouter"],
            "claude-opus-4-1": ["anthropic"],
            "gpt-5": ["openrouter", "openai"],
            "google/gemini-2.5-pro": ["openrouter"],
            "gemini-2.5-pro": ["gemini"]
        }
    
    def _initialize_providers(self) -> Dict[str, LLMProvider]:
        providers = {}
        
        # OpenRouter
        if settings.openrouter_api_key:
            providers["openrouter"] = OpenRouterProvider(
                settings.openrouter_api_key,
                settings.openrouter_url
            )
        
        # Anthropic
        if settings.anthropic_api_key:
            providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
        
        
        # OpenAI
        if settings.openai_api_key:
            providers["openai"] = OpenAIProvider(settings.openai_api_key)
        
        
        # Gemini
        if settings.gemini_api_key:
            providers["gemini"] = GeminiProvider(settings.gemini_api_key, "https://generativelanguage.googleapis.com/v1beta/openai/")
        
        
        return providers
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        """Generate response with fallback through models and providers."""
        
        for model in settings.model_preferences:
            available_providers = self.model_mapping.get(model, [])
            
            for provider_name in available_providers:
                if provider_name not in self.providers:
                    continue
                
                provider = self.providers[provider_name]
                if not provider.is_available():
                    continue
                
                try:
                    logger.info(f"Attempting generation with {model} via {provider_name}")
                    response = await provider.generate(
                        prompt=prompt,
                        model=model,
                        system_prompt=system_prompt,
                        attachments=attachments
                    )
                    logger.info(f"Successfully generated with {model} via {provider_name}")
                    return response
                except Exception as e:
                    logger.error(f"Failed with {model} via {provider_name}: {str(e)}")
                    continue
        
        raise Exception("All LLM providers failed. Please check your API keys and configurations.")