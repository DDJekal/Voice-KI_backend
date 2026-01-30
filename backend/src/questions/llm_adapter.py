"""
Unified LLM Adapter - Claude Primary, OpenAI Fallback

Provides a unified interface for LLM calls with automatic fallback
from Claude to OpenAI if Claude fails or times out.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)


async def call_llm_async(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    response_format: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    force_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified LLM Call mit Claude (Primary) + OpenAI (Fallback).
    
    Args:
        messages: List of messages with role and content
        temperature: Temperature parameter (0-2)
        response_format: Response format for JSON mode (OpenAI only)
        timeout: Optional timeout override (default: from config)
        force_provider: Force specific provider ("claude" or "openai") for A/B testing
        
    Returns:
        Unified response dict:
        {
            "choices": [{"message": {"content": "...", "role": "assistant"}}],
            "usage": {"total_tokens": 123, "input_tokens": 50, "output_tokens": 73},
            "_provider": "claude" | "openai",
            "_duration": 8.5
        }
        
    Raises:
        Exception: If all providers fail
        TimeoutError: If timeout exceeded for all providers
    """
    settings = get_settings()
    timeout_seconds = timeout or settings.llm_timeout_seconds
    start_time = time.time()
    
    # Determine provider order
    if force_provider:
        providers = [force_provider]
    elif settings.use_claude_first and settings.anthropic_api_key:
        providers = ["claude"]
        if settings.openai_api_key:
            providers.append("openai")
    elif settings.openai_api_key:
        providers = ["openai"]
    else:
        providers = []
    
    if not providers:
        raise ValueError(
            "Kein LLM Provider konfiguriert! "
            "Bitte ANTHROPIC_API_KEY oder OPENAI_API_KEY in .env setzen"
        )
    
    last_error = None
    
    for provider in providers:
        try:
            logger.info(f"LLM Call: {provider.upper()} (timeout: {timeout_seconds}s)")
            
            if provider == "claude":
                result = await asyncio.wait_for(
                    _call_claude(messages, temperature, settings),
                    timeout=timeout_seconds
                )
            else:  # openai
                result = await asyncio.wait_for(
                    _call_openai(messages, temperature, response_format, settings),
                    timeout=timeout_seconds
                )
            
            duration = time.time() - start_time
            tokens = result.get("usage", {}).get("total_tokens", 0)
            
            logger.info(f"LLM Success: {provider.upper()}, {duration:.1f}s, {tokens} tokens")
            result["_provider"] = provider
            result["_duration"] = duration
            
            return result
            
        except asyncio.TimeoutError:
            last_error = f"{provider} timeout after {timeout_seconds}s"
            logger.warning(f"LLM Timeout: {last_error}")
            continue
            
        except Exception as e:
            last_error = f"{provider} error: {str(e)}"
            logger.warning(f"LLM Error: {last_error}")
            continue
    
    # All providers failed
    raise Exception(f"Alle LLM Provider fehlgeschlagen. Letzter Fehler: {last_error}")


async def _call_claude(
    messages: List[Dict[str, str]],
    temperature: float,
    settings
) -> Dict[str, Any]:
    """
    Internal call to Claude API.
    
    Claude expects system message separately from user messages.
    Note: Claude doesn't support response_format like OpenAI, so we need
    to handle JSON extraction from the response.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    # Claude expects system message separately
    system_msg = None
    user_messages = []
    
    for msg in messages:
        if msg["role"] == "system":
            # Add explicit JSON instruction to system message
            system_content = msg["content"]
            if "json" not in system_content.lower():
                system_content += "\n\nWICHTIG: Antworte NUR mit validem JSON. Keine Erklärungen, kein Markdown, nur das JSON-Objekt."
            system_msg = system_content
        else:
            user_messages.append(msg)
    
    # Build API call kwargs
    kwargs = {
        "model": settings.anthropic_model,
        "max_tokens": 8192,  # Enough for large JSON responses
        "temperature": temperature,
        "messages": user_messages
    }
    
    if system_msg:
        kwargs["system"] = system_msg
    
    # Make API call
    response = await client.messages.create(**kwargs)
    
    # Extract content
    raw_content = response.content[0].text
    
    # Try to extract JSON from response (Claude sometimes wraps in markdown)
    content = _extract_json_from_response(raw_content)
    
    # Convert to unified format (OpenAI-compatible)
    return {
        "choices": [{
            "message": {
                "content": content,
                "role": "assistant"
            }
        }],
        "usage": {
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        }
    }


def _extract_json_from_response(text: str) -> str:
    """
    Extract JSON from Claude response, handling markdown code blocks.
    
    Claude sometimes wraps JSON in ```json ... ``` blocks.
    """
    import re
    
    # Try to find JSON in code blocks first
    json_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(json_block_pattern, text)
    
    if matches:
        # Return the first JSON-like block
        for match in matches:
            stripped = match.strip()
            if stripped.startswith('{') or stripped.startswith('['):
                return stripped
    
    # If no code block, try to find JSON directly
    text = text.strip()
    
    # Find the first { or [ and last } or ]
    start_brace = text.find('{')
    start_bracket = text.find('[')
    
    if start_brace == -1 and start_bracket == -1:
        return text  # No JSON found, return as-is
    
    if start_brace == -1:
        start = start_bracket
        end_char = ']'
    elif start_bracket == -1:
        start = start_brace
        end_char = '}'
    else:
        start = min(start_brace, start_bracket)
        end_char = '}' if start == start_brace else ']'
    
    # Find matching end
    end = text.rfind(end_char)
    
    if end > start:
        return text[start:end + 1]
    
    return text


async def _call_openai(
    messages: List[Dict[str, str]],
    temperature: float,
    response_format: Optional[Dict[str, str]],
    settings
) -> Dict[str, Any]:
    """
    Internal call to OpenAI API.
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    kwargs = {
        "model": settings.openai_model,
        "temperature": temperature,
        "messages": messages
    }
    
    if response_format:
        kwargs["response_format"] = response_format
    
    response = await client.chat.completions.create(**kwargs)
    result = response.model_dump()
    
    # Ensure usage keys exist
    if "usage" not in result:
        result["usage"] = {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0}
    
    return result


# Legacy compatibility - can be used as drop-in replacement
async def call_openai_async(
    model: str,
    temperature: float,
    messages: List[Dict[str, str]],
    response_format: Dict[str, str]
) -> Dict[str, Any]:
    """
    Legacy wrapper for backward compatibility.
    
    Redirects to unified call_llm_async with OpenAI forced.
    Use call_llm_async directly for new code.
    """
    return await call_llm_async(
        messages=messages,
        temperature=temperature,
        response_format=response_format,
        force_provider="openai"
    )
