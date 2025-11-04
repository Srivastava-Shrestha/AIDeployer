# app/services/deployment.py
import httpx
import asyncio
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from app.models.schemas import EvaluationResponseSchema

logger = logging.getLogger(__name__)

class DeploymentService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=8)
    )
    async def notify_evaluation(self, evaluation_url: str, data: EvaluationResponseSchema) -> bool:
        """Send evaluation response with retry logic."""
        try:
            response = await self.client.post(
                evaluation_url,
                json=data.model_dump(),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully notified evaluation API")
                return True
            else:
                logger.error(f"Evaluation API returned {response.status_code}: {response.text}")
                raise Exception(f"Non-200 response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error notifying evaluation API: {str(e)}")
            raise
    
    async def wait_for_pages_deployment(self, pages_url: str, max_wait: int = 300) -> bool:
        """Wait for GitHub Pages to be accessible."""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < max_wait:
            try:
                response = await self.client.get(pages_url)
                if response.status_code == 200:
                    logger.info(f"GitHub Pages is accessible at {pages_url}")
                    return True
            except:
                pass
            
            await asyncio.sleep(5)
        
        logger.warning(f"GitHub Pages not accessible after {max_wait} seconds")
        return False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()