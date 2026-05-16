import re

def sanitize_error(error_msg: str) -> str:
    """
    Removes API keys and other sensitive information from error messages.
    Searches for common API key patterns (like Gemini/Google AI keys).
    """
    if not error_msg:
        return ""
    
    # Redact Google AI API keys (usually start with AIza)
    sanitized = re.sub(r'key=AIza[a-zA-Z0-9_\-]+', 'key=[REDACTED]', error_msg)
    
    # Also catch generic API keys in URLs
    sanitized = re.sub(r'api_key=[a-zA-Z0-9_\-]+', 'api_key=[REDACTED]', sanitized)
    
    return sanitized
