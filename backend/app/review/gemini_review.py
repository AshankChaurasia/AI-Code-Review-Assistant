import google.generativeai as genai
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not found in .env file")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # List available models for debugging
        for m in genai.list_models():
            logger.info(f"Available model: {m.name}")
    except Exception as e:
        logger.warning(f"Gemini configuration failed: {e}")


def gemini_code_review(code: str, static_results: str = "") -> list:
    """
    Perform AI-powered code review using Gemini API.
    Returns a list of review items.
    """
    if not GEMINI_API_KEY:
        return [{
            "category": "Error",
            "line": "N/A",
            "message": "GEMINI_API_KEY not found in .env file",
            "suggestion": "Add GEMINI_API_KEY to your .env file"
        }]

    try:
        prompt = f"""You are an expert Python code reviewer. Respond ONLY with a valid JSON array of review items.
If no issues, return [].
Each item must follow this schema exactly:
{{
  "category": "Bug | Performance | Style | Security | Readability | BestPractice",
  "line": "<Line number or 'N/A'>",
  "message": "Brief description of the issue",
  "suggestion": "Clear, actionable fix suggestion"
}}

Static Analysis Results:
{static_results}

Python Code to Review:
```python
{code}
```

Provide a detailed code review."""

        # Attempt to use 'gemini-pro-latest' first
        model_name = 'gemini-pro-latest'
        text = None

        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = response.text.strip()
            logger.info(f"Raw Gemini output using {model_name}: {text[:500]}")
        except Exception as e:
            logger.warning(f"Failed to use {model_name}: {e}")

            # If 'gemini-pro-latest' fails, try 'gemini-pro' as a fallback
            model_name = 'gemini-pro'
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                text = response.text.strip()
                logger.info(f"Raw Gemini output using {model_name}: {text[:500]}")
            except Exception as e2:
                logger.error(f"Failed to use {model_name} as fallback: {e2}")
                raise e2

        # Clean up response text
        if text.startswith("```"):
            text = text[text.find("\n")+1:text.rfind("```")].strip()
        if text.startswith("json"):
            text = text[4:].strip()

        try:
            reviews = json.loads(text)
            if not isinstance(reviews, list):
                reviews = [reviews]
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from Gemini: {text[:300]}...")
            return [{
                "category": "Error",
                "line": "N/A",
                "message": "Invalid response format from AI",
                "suggestion": f"Raw response: {text[:200]}"
            }]

        validated_reviews = []
        for item in reviews:
            if isinstance(item, dict):
                validated_reviews.append({
                    "category": item.get("category", "Unknown"),
                    "line": item.get("line", "N/A"),
                    "message": item.get("message", "No message provided"),
                    "suggestion": item.get("suggestion", "No suggestion provided")
                })

        return validated_reviews if validated_reviews else [{
            "category": "Info",
            "line": "N/A",
            "message": "No issues found",
            "suggestion": "Code looks good!"
        }]

    except Exception as e:
        logger.exception("Gemini API error")
        error_type = type(e).__name__
        error_message = str(e)

        # Fallback to basic review message
        return [{
            "category": "Error",
            "line": "N/A",
            "message": f"AI Review failed: {error_type}",
            "suggestion": f"Gemini API error: {error_message}. Please check your API key, model availability, and API quota."
        }]