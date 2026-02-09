import os
import json
import requests
import google.generativeai as genai
import time

# --- CONFIGURATION ---
# API Key GitHub Secrets se aayegi
API_KEY = os.environ.get("GEMINI_API_KEY")

# Aapki News File ka Raw Link (2.json)
NEWS_SOURCE_URL = "https://raw.githubusercontent.com/GOLutheGhosT-4444/Today-Current-Affairs/refs/heads/main/2.json"
OUTPUT_FILE = "quiz.json"

# --- 1. FETCH NEWS DATA ---
def fetch_news():
    print(f"📥 Fetching news from: {NEWS_SOURCE_URL}")
    try:
        response = requests.get(NEWS_SOURCE_URL)
        response.raise_for_status()
        
        try:
            data = response.json()
            # Saari news ka content combine karein context ke liye
            combined_text = ""
            for item in data:
                content = item.get('content', '') or item.get('summary', '')
                if len(content) > 50:
                    combined_text += content + "\n---\n"
            
            print(f"✅ News fetched successfully! Length: {len(combined_text)} chars")
            return combined_text
        except json.JSONDecodeError:
            print("❌ Error: 2.json is not valid JSON. Trying to read as raw text.")
            return response.text
            
    except Exception as e:
        print(f"❌ Network Error: {e}")
        return None

# --- 2. GENERATE PROFESSIONAL QUESTIONS ---
def generate_quiz(news_text):
    if not API_KEY:
        print("❌ Error: GEMINI_API_KEY not found in environment variables.")
        return None

    if not news_text or len(news_text) < 100:
        print("❌ Not enough news data to generate quiz.")
        return None

    print("🤖 Sending data to Gemini AI for Question Generation...")
    
    genai.configure(api_key=API_KEY)
    
    # Use 'gemini-1.5-flash' for speed and large context
    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- PROMPT ENGINEERING (THE SECRET SAUCE) ---
    prompt = f"""
    You are a Senior Question Setter for IBPS PO and SBI PO Banking Exams. 
    Analyze the provided news text and generate 10-15 High-Level Multiple Choice Questions (MCQs).

    CONTEXT DATA:
    {news_text[:12000]} 

    STRICT GUIDELINES:
    1. **Difficulty:** Hard/Professional. Focus on economic figures, RBI guidelines, exact dates, and tricky appointments.
    2. **Options:** Must be very confusing. 
       - If the answer is "6.5%", options should be ["6.25%", "6.5%", "6.65%", "6.4%"].
       - Include "None of these" as an option in 20% of questions.
    3. **Format:** Output MUST be a raw JSON Array. Do not use Markdown (```json).
    4. **Structure:**
       [
         {{
           "q": "Question text here?",
           "a": "Correct Answer",
           "options": ["Option A", "Option B", "Correct Answer", "Option D", "Option E"],
           "cat": "Category (e.g., Banking, Economy, National)"
         }}
       ]
    5. Ensure the "a" (answer) is exactly present in the "options" list.
    """

    try:
        response = model.generate_content(prompt)
        
        # Clean the response (Remove markdown if AI adds it)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        
        # Validate JSON
        quiz_data = json.loads(clean_text)
        print(f"✅ Generated {len(quiz_data)} professional questions.")
        return quiz_data

    except Exception as e:
        print(f"❌ AI Generation Error: {e}")
        print("Raw Response:", response.text if 'response' in locals() else "No response")
        return None

# --- 3. SAVE TO FILE ---
def save_file(data):
    if data:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"💾 Quiz saved to {OUTPUT_FILE}")
    else:
        print("⚠️ No data to save.")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    news_content = fetch_news()
    if news_content:
        quiz_json = generate_quiz(news_content)
        if quiz_json:
            save_file(quiz_json)
        else:
            # Fallback: Create a dummy file so workflow doesn't fail completely
            print("⚠️ Generating fallback empty JSON")
            save_file([])
    else:
        print("❌ Process failed at fetching stage.")
