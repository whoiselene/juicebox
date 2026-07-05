import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables (useful when running standalone or in development)
load_dotenv()

def rewrite_cover_letter(text, original_score, api_key=None):
    """
    Calls the Gemini API to rewrite the cover letter, stripping jargon and highlighting metrics.
    Returns a dictionary conforming to the payload schema.
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        return {
            "status": "error",
            "message": "Gemini API key is not configured. Please set GEMINI_API_KEY in a .env file in the project root."
        }
    
    try:
        genai.configure(api_key=api_key)
        
        # Using gemini-1.5-flash for fast performance and general availability
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        
        prompt = f"""
        You are Project Papaya's Generative Rewrite Engine. Your task is to analyze a cover letter, strip out the hollow corporate jargon/clichés, and rewrite it into a highly compelling, narrative-driven career introduction.
        
        Guidelines:
        1. Eliminate empty buzzwords (e.g., 'highly motivated', 'results-oriented', 'proven track record', 'synergistic alignment').
        2. Keep the hard technical skills, engineering/project metrics, and core achievements intact.
        3. Write in a warm-minimalist, tactile, retro-modern editorial tone (clear, concise, authentic, and expressive).
        4. Identify the specific jargon phrases that you removed or replaced, and provide a short, constructive reason for why they were flagged.
        
        The original text robot score was calculated as {original_score}%.
        
        Original Cover Letter text:
        \"\"\"{text}\"\"\"
        
        You MUST respond with a JSON object conforming exactly to this schema:
        {{
          "status": "success",
          "original_score": {original_score},
          "rewritten_output": "String representing clean, narrative-driven text.",
          "flags": [
            {{
              "phrase": "jargon phrase found",
              "reason": "Constructive reason explaining why it is devalued and what to focus on instead."
            }}
          ]
        }}
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse output JSON to ensure validity
        data = json.loads(response_text)
        
        # Ensure status field exists
        if "status" not in data:
            data["status"] = "success"
        if "original_score" not in data:
            data["original_score"] = original_score
            
        return data
        
    except json.JSONDecodeError as jde:
        return {
            "status": "error",
            "message": f"Gemini API returned invalid JSON: {str(jde)}. Raw response: {response.text if 'response' in locals() else 'None'}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to rewrite cover letter via Gemini API: {str(e)}"
        }
