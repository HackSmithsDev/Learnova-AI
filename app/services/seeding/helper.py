import os
import json
import time
from groq import Groq
from config import Config

# Initialize Client - Good call using getenv for security!
client = Groq(api_key=Config.GROQ_API_KEY)

def call_groq(prompt: str, response_model):
    """
    Sends a prompt to Groq and forces the response into the 
    provided Pydantic model structure.
    """
    # Prof Tip: 70B is great, but it can be slow. 
    # Let's add a small retry logic in case of a 503/timeout
    max_retries = 3
    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a Senior University Professor. "
                            "Return ONLY valid JSON. Do not include markdown or explanations. "
                            f"Strict Schema: {response_model.model_json_schema()}"
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                model=Config.GROQ_MODEL,
                response_format={"type": "json_object"},
                temperature=0.6 # Lowered slightly for more consistent academic facts
            )
            
            # Parse the JSON
            raw_data = json.loads(chat_completion.choices[0].message.content)
            
            # 2026 Validation: We ensure it's not an empty object
            if not raw_data:
                raise ValueError("AI returned an empty JSON object")
                
            return raw_data
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                print(f"⏳ Rate limit hit. Waiting 10s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(10)
            else:
                print(f"🛑 Attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(2)
    return None