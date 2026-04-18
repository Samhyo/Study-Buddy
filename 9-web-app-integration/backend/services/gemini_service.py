import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite") #gemini-2.5-flash-lite #gemma4-31b-it

async def generate_quiz(text_context: str):
    # Ensure we actually have text
    if not text_context.strip():
        return {"error": "No text could be extracted from the PDF."}

    # High-pressure prompt to force JSON and ignore the "file upload" concept
    prompt = f"""
    SYSTEM INSTRUCTIONS: 
    You are a JSON-generating study engine. Do not engage in conversation. 
    You will be provided with text extracted from a document. 
    Your task is to create a 3-question quiz based on this text.

    EXTRACTED TEXT START:
    {text_context[:8000]}
    EXTRACTED TEXT END:

    OUTPUT FORMAT:
    Return ONLY a valid JSON array of objects. No intro text, no markdown backticks.
    Format:
    [
      {{
        "question": "string",
        "options": ["string", "string", "string", "string"],
        "correct_answer": "string",
        "explanation": "string"
      }}
    ]
    """

    try:
        response = model.generate_content(prompt)
        # Force clean the text
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Gemini Error: {e}")
        return [{"question": "Error", "options": [str(e)], "correct_answer": "Error", "explanation": "Error"}]
    