"""
OpenAI API Adapter

Port of TypeScript openai adapter for Python.
"""

from typing import Dict, Any, List
import logging
from openai import OpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)


def call_openai(
    model: str,
    temperature: float,
    messages: List[Dict[str, str]],
    response_format: Dict[str, str]
) -> Dict[str, Any]:
    """
    Call OpenAI API with given parameters.
    
    Args:
        model: Model name (e.g. "gpt-4o")
        temperature: Temperature parameter (0-2)
        messages: List of messages with role and content
        response_format: Response format (e.g. {"type": "json_object"})
        
    Returns:
        API response as dict
        
    Raises:
        Exception: If API call fails
    """
    settings = get_settings()
    
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")
    
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        logger.info(f"Calling OpenAI API: model={model}, temperature={temperature}, messages={len(messages)}")
        
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages,
            response_format=response_format
        )
        
        result = response.model_dump()
        
        logger.info(f"OpenAI API response received: {result['usage']['total_tokens']} tokens")
        
        return result
        
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise Exception(f"OpenAI API error: {e}")


async def call_openai_async(
    model: str,
    temperature: float,
    messages: List[Dict[str, str]],
    response_format: Dict[str, str]
) -> Dict[str, Any]:
    """
    Async wrapper for OpenAI API call.
    
    Args:
        model: Model name (e.g. "gpt-4o")
        temperature: Temperature parameter (0-2)
        messages: List of messages with role and content
        response_format: Response format (e.g. {"type": "json_object"})
        
    Returns:
        API response as dict
        
    Raises:
        Exception: If API call fails
    """
    # For now, just call synchronous version
    # OpenAI Python SDK has async support, but keeping it simple
    return call_openai(model, temperature, messages, response_format)

