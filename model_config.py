"""
Model Configuration for AI Healthcare Assistant
This file centralizes model selection to easily switch between different AI models
"""

import os
from typing import Dict, Any

class ModelConfig:
    """Centralized model configuration"""
    
    # Available models with their characteristics
    AVAILABLE_MODELS = {
        "gemini-1.5-flash": {
            "name": "gemini-1.5-flash",
            "description": "Fast and reliable Gemini model",
            "max_tokens": 8192,
            "temperature": 0.7,
            "reliability": "high",
            "speed": "fast"
        },
        "gemini-1.5-pro": {
            "name": "gemini-1.5-pro", 
            "description": "More capable but slower Gemini model",
            "max_tokens": 32768,
            "temperature": 0.7,
            "reliability": "high",
            "speed": "medium"
        },
        "gemini-2.0-flash": {
            "name": "gemini-2.0-flash",
            "description": "Latest Gemini model (may be overloaded)",
            "max_tokens": 8192,
            "temperature": 0.7,
            "reliability": "medium",
            "speed": "fast"
        },
        "gemini-1.0-pro": {
            "name": "gemini-1.0-pro",
            "description": "Stable older Gemini model",
            "max_tokens": 30720,
            "temperature": 0.7,
            "reliability": "high",
            "speed": "medium"
        }
    }
    
    # Default model (most reliable)
    DEFAULT_MODEL = "gemini-1.5-flash"
    
    # Fallback models in order of preference
    FALLBACK_MODELS = [
        "gemini-1.5-flash",
        "gemini-1.5-pro", 
        "gemini-1.0-pro",
        "gemini-2.0-flash"
    ]
    
    @classmethod
    def get_model_name(cls, model_key: str = None) -> str:
        """Get the model name to use"""
        if model_key and model_key in cls.AVAILABLE_MODELS:
            return cls.AVAILABLE_MODELS[model_key]["name"]
        
        # Try environment variable
        env_model = os.getenv("GEMINI_MODEL", cls.DEFAULT_MODEL)
        if env_model in cls.AVAILABLE_MODELS:
            return cls.AVAILABLE_MODELS[env_model]["name"]
        
        return cls.AVAILABLE_MODELS[cls.DEFAULT_MODEL]["name"]
    
    @classmethod
    def get_model_config(cls, model_key: str = None) -> Dict[str, Any]:
        """Get full model configuration"""
        model_name = cls.get_model_name(model_key)
        return cls.AVAILABLE_MODELS.get(model_name, cls.AVAILABLE_MODELS[cls.DEFAULT_MODEL])
    
    @classmethod
    def get_fallback_models(cls) -> list:
        """Get list of fallback models"""
        return cls.FALLBACK_MODELS
    
    @classmethod
    def is_model_available(cls, model_key: str) -> bool:
        """Check if a model is available"""
        return model_key in cls.AVAILABLE_MODELS
    
    @classmethod
    def get_model_info(cls, model_key: str = None) -> str:
        """Get human-readable model information"""
        config = cls.get_model_config(model_key)
        return f"{config['name']} - {config['description']} (Reliability: {config['reliability']}, Speed: {config['speed']})"

# Global model configuration
MODEL_CONFIG = ModelConfig()

def get_gemini_model(model_key: str = None):
    """Get configured Gemini model instance"""
    import google.generativeai as genai
    
    model_name = MODEL_CONFIG.get_model_name(model_key)
    print(f"🤖 Using AI model: {model_name}")
    
    try:
        model = genai.GenerativeModel(model_name)
        return model
    except Exception as e:
        print(f"❌ Error loading model {model_name}: {e}")
        # Try fallback models
        for fallback_model in MODEL_CONFIG.get_fallback_models():
            if fallback_model != model_name:
                try:
                    print(f"🔄 Trying fallback model: {fallback_model}")
                    model = genai.GenerativeModel(fallback_model)
                    print(f"✅ Successfully loaded fallback model: {fallback_model}")
                    return model
                except Exception as fallback_error:
                    print(f"❌ Fallback model {fallback_model} also failed: {fallback_error}")
                    continue
        
        # If all models fail, raise the original error
        raise e

def get_model_with_retry(model_key: str = None, max_retries: int = 3):
    """Get model with retry logic for overloaded models"""
    import time
    import google.generativeai as genai
    
    for attempt in range(max_retries):
        try:
            model = get_gemini_model(model_key)
            return model
        except Exception as e:
            error_msg = str(e).lower()
            if "overloaded" in error_msg or "unavailable" in error_msg or "503" in error_msg:
                print(f"⚠️ Model overloaded (attempt {attempt + 1}/{max_retries}), trying fallback...")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            else:
                # Non-overload error, don't retry
                raise e
    
    # If we get here, all retries failed
    raise Exception("All models are currently overloaded. Please try again later.") 