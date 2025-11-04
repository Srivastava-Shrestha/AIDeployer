# app/services/llm/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None

class LLMProvider(ABC):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        model: str,
        system_prompt: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass