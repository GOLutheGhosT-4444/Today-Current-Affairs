import os
import json
import requests
import google.generativeai as genai
import sys

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
NEWS_SOURCE = "https://raw.githubusercontent.com/GOLutheGhosT-4444/Today-Current-Affairs/refs/heads/main/2.json"
OUTPUT_FILE = "quiz.json"

# --- 1. AUTO-DETECT BEST MODEL ---
def get_available_model():
    if not API_KEY:
        print("❌ CRITICAL ERROR: GEMINI_API_KEY not found in Secrets!")
        sys.exit(1)

    genai.configure(api_key=API_KEY)

    print("🔍 Scanning available AI models for your API Key...")
    try:
        # Ask Google: "Kaunse models available hain?"
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        print(f"📋 Found Models: {available_models}")

        # Priority Selection (Jo best hai wo pehle chuno)
        # Priority: 1.5-pro > 1.5-flash > pro > others
        preferred_order = [
            "models/gemini-1.5-pro",
            "models/gemini-1.5-flash", 
            "models/gemini-pro"
        ]

        for model in preferred_order:
            if model in available_models:
                print(f"✅ SELECTED BEST MODEL: {model}")
                return model
        
        # Agar preferred me se koi nahi mila, to list ka pehla utha lo
        if available_models:
            print(f"⚠️ Preferred models not found. Using fallback: {available_models[0]}")
            return available_models[0]
            
        print("❌ No text-generation models found for this API Key.")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Error listing models: {e}")
        sys.exit(1)

# --- 2. FETCH NEWS ---
def fetch_news():
    print(f"📥 Fetching News from: {NEWS_SOURCE}")
    try:
        response = requests.get(NEWS_SOURCE)
        response.raise_for_status()
        
        try:
            data = response.json()
            text_data = ""
            for item in data:
                content = item.get('content', '') or item.get('summary', '')
                if len(content) > 50:
                    text_data += f"- {content}\n"
            
            if len(text_data) < 100:
                print("❌ News data is too short or empty.")
                sys.exit(1)

            print(f"✅ News Loaded. Length: {len(text_data)} chars")
            return text_data
        except json.JSONDecodeError:
            print("❌ JSON Error in News Source.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Network Error: {e}")
        sys.exit(1)

# --- 3. GENERATE QUIZ ---
def generate_questions(news_text, model_name):
    # Configure with the detected model
    model = genai.GenerativeModel(model_name)

    print("🧠 Starting Generation (No Backup Mode)...")

    prompt = f"""
    You are a Ruthless Banking Exam Setter (IBPS/SBI PO Level).
    I need exactly 60 One-Liner MCQs based on the news text provided below.

    ### STRICT QUESTION CRITERIA (The 5 Pillars):
    Generate questions ONLY related to these 5 categories:
    1. **Amount:** (Budget, GDP, Loans, Penalties, Deal Value) - *Most Important*
    2. **Who (Kisne):** (Appointments, Resignations, Award Winners)
    3. **Where (Kha):** (Summit Venues, HQs, Inauguration Places)
    4. **When (Kab):** (Target Years, Days celebrated, Deadlines)
    5. **Why (Kyo):** (Themes of days, Purpose of schemes, Motto)

    ### STRICT OPTION CRITERIA (Confusing Levels):
    - Create exactly 5 Options for each question.
    - One correct, Four extreme distractors.
    - *Example (Amount):* If Answer "Rs 500 Cr", Options: ["Rs 510 Cr", "Rs 490 Cr", "Rs 500 Cr", "Rs 505 Cr", "Rs 495 Cr"]

    ### OUTPUT FORMAT:
    - Return a RAW JSON Array.
    - Structure: [{{"q": "Question", "a": "Correct Answer", "options": ["A", "B", "C", "D", "E"], "cat": "Category"}}]
    - Generate 60 items.

    ### NEWS DATA:
    {news_text[:28000]}
    """

    try:
        response = model.generate_content(prompt)
        
        # Clean Markdown
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        
        # Validate
        quiz_data = json.loads(clean_json)
        
        count = len(quiz_data)
        print(f"⚡ AI Generated {count} Questions.")
        
        if count < 5:
            print("❌ Error: AI generated junk or too few questions.")
            sys.exit(1) # Crash workflow

        return quiz_data

    except Exception as e:
        print(f"❌ AI Critical Error: {e}")
        sys.exit(1) # Crash workflow

# --- 4. SAVE FILE ---
def save_quiz(data):
    if not data:
        print("❌ No data generated.")
        sys.exit(1)

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"💾 Successfully saved {len(data)} REAL questions to {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ File Save Error: {e}")
        sys.exit(1)

# --- EXECUTION ---
if __name__ == "__main__":
    # Step 1: Find best model
    best_model = get_available_model()
    
    # Step 2: Get News
    news = fetch_news()
    
    # Step 3: Generate
    questions = generate_questions(news, best_model)
    
    # Step 4: Save
    save_quiz(questions)
