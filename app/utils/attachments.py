# app/utils/attachments.py
import base64
import re
from typing import Tuple, Optional, Dict, Any
import httpx
from pathlib import Path
import mimetypes

class AttachmentHandler:
    @staticmethod
    def parse_data_uri(data_uri: str) -> Tuple[str, str, bytes]:
        """Parse a data URI and return mime_type, encoding, and data."""
        # Pattern: data:[<mediatype>][;base64],<data>
        pattern = r'data:([^;]+)(;base64)?,(.+)'
        match = re.match(pattern, data_uri)
        
        if not match:
            raise ValueError(f"Invalid data URI format")
        
        mime_type = match.group(1) or 'text/plain'
        is_base64 = match.group(2) is not None
        data_part = match.group(3)
        
        if is_base64:
            data = base64.b64decode(data_part)
        else:
            data = data_part.encode('utf-8')
        
        return mime_type, 'base64' if is_base64 else 'plain', data
    
    @staticmethod
    async def process_attachment(attachment: Dict[str, str]) -> Dict[str, Any]:
        """Process an attachment and return its content and metadata."""
        url = attachment['url']
        name = attachment['name']
        
        if url.startswith('data:'):
            # Handle data URI
            mime_type, encoding, data = AttachmentHandler.parse_data_uri(url)
            return {
                'name': name,
                'mime_type': mime_type,
                'content': data,
                'is_binary': not mime_type.startswith('text/'),
                'source': 'data_uri'
            }
        else:
            # Handle regular URL
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                
                mime_type = response.headers.get('content-type', 'application/octet-stream')
                return {
                    'name': name,
                    'mime_type': mime_type,
                    'content': response.content,
                    'is_binary': not mime_type.startswith('text/'),
                    'source': 'url'
                }
    
    @staticmethod
    def decode_text_content(content: bytes, mime_type: str) -> str:
        """Decode text content based on mime type."""
        if mime_type.startswith('text/') or mime_type in ['application/json', 'application/xml']:
            return content.decode('utf-8', errors='replace')
        return base64.b64encode(content).decode('ascii')