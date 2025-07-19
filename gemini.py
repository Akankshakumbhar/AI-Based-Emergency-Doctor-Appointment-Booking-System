import time
import os
import google.generativeai as genai
from model_config import get_model_with_retry
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")
genai.configure(api_key=api_key)

class QuotaExhaustedError(Exception):
    """Custom exception for quota exhaustion"""
    pass

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_gemini_with_retry(prompt: str, temperature: float = 0.7, max_output_tokens: int = 1000, top_p: float = 0.8, top_k: int = 40) -> str:
    try:
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=top_p,
            top_k=top_k
        )
        
        model = get_model_with_retry()
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        return response.text
    except Exception as e:
        error_str = str(e)
        
        # Check for quota exhaustion
        if "429" in error_str and "quota" in error_str.lower():
            logger.error("🚨 Google Gemini API quota exhausted!")
            logger.error("💡 Solutions:")
            logger.error("   1. Wait for quota reset (24 hours)")
            logger.error("   2. Use a different API key")
            logger.error("   3. Upgrade to paid tier")
            raise QuotaExhaustedError(f"API quota exhausted: {error_str}")
        
        # Check for invalid API key
        if "401" in error_str or "invalid" in error_str.lower():
            logger.error("🚨 Invalid API key!")
            logger.error("💡 Please check your GOOGLE_API_KEY environment variable")
            raise ValueError(f"Invalid API key: {error_str}")
        
        # Generic error handling
        logger.error(f"🚨 Error calling Gemini API: {error_str}")
        raise Exception(f"Error calling Gemini API: {str(e)}")

def call_gemini_safe(prompt: str, fallback_response: str = None, **kwargs) -> str:
    """
    Safe wrapper that provides fallback responses when API fails
    """
    try:
        return call_gemini_with_retry(prompt, **kwargs)
    except QuotaExhaustedError:
        if fallback_response:
            logger.warning(f"🔄 Using fallback response due to quota exhaustion")
            return fallback_response
        else:
            return "⚠️ API quota exhausted. Please try again later or upgrade your plan."
    except Exception as e:
        if fallback_response:
            logger.warning(f"🔄 Using fallback response due to error: {e}")
            return fallback_response
        else:
            return f"⚠️ Service temporarily unavailable: {str(e)}" 