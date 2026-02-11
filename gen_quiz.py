import os
import json
import requests
import google.generativeai as genai
import time

# --- CONFIGURATION ---
# GitHub Secrets se API Key
API_KEY = os.environ.get("GEMINI_API_KEY")
NEWS_SOURCE = "https://raw.githubusercontent.com/GOLutheGhosT-4444/Today-Current-Affairs/refs/heads/main/2.json"
OUTPUT_FILE = "quiz.json"

# --- 1. FETCH DATA ---
def fetch_news():
    print(f"📥 Fetching Raw Data from: {NEWS_SOURCE}")
    try:
        response = requests.get(NEWS_SOURCE)
        response.raise_for_status()
        
        try:
            data = response.json()
            # Combine content for context
            text_data = ""
            for item in data:
                content = item.get('content', '') or item.get('summary', '')
                if len(content) > 50:
                    text_data += f"- {content}\n"
            
            print(f"✅ Data Loaded. Total Chars: {len(text_data)}")
            return text_data
        except json.JSONDecodeError:
            print("⚠️ JSON Error. Using Raw Text.")
            return response.text
            
    except Exception as e:
        print(f"❌ Error Fetching Data: {e}")
        return None

# --- 2. GENERATE POWERFUL QUESTIONS ---
def generate_questions(news_text):
    if not API_KEY:
        print("❌ Error: GEMINI_API_KEY Missing!")
        return []

    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    print("🧠 Starting AI Generation (Target: 60 Questions)...")

    # Prompt Engineering: The Brain of the Script
    prompt = f"""
    You are a Ruthless Banking Exam Paper Setter (IBPS/SBI PO Level).
    I need exactly 60 One-Liner MCQs based on the news text provided below.

    ### STRICT QUESTION CRITERIA (The 5 Pillars):
    Generate questions ONLY related to these 5 categories:
    1. **Amount:** (Budget, GDP, Loans, Penalties, Deal Value) - *Most Important*
    2. **Who (Kisne):** (Appointments, Resignations, Award Winners, Partners)
    3. **Where (Kha):** (Summit Venues, HQs, Inauguration Places)
    4. **When (Kab):** (Target Years, Days celebrated, Deadlines)
    5. **Why (Kyo):** (Themes of days, Purpose of schemes, Motto)

    ### STRICT OPTION CRITERIA (Confusing Levels):
    - Create exactly 5 Options for each question.
    - **One** must be correct.
    - **Four** must be extreme distractors.
    - *Example (Amount):* If Answer is "Rs 500 Cr", Options: ["Rs 510 Cr", "Rs 490 Cr", "Rs 500 Cr", "Rs 505 Cr", "Rs 495 Cr"]
    - *Example (Date):* If Answer is "24 Jan", Options: ["23 Jan", "25 Jan", "24 Jan", "22 Jan", "21 Jan"]
    - *Example (Name):* If Answer is "Amit Shah", Options: ["Rajnath Singh", "Amit Shah", "Nitin Gadkari", "Piyush Goyal", "J.P. Nadda"]

    ### OUTPUT FORMAT:
    - Return a RAW JSON Array.
    - Structure: {{"q": "Question", "a": "Correct Answer", "options": ["A", "B", "C", "D", "E"], "cat": "Category"}}
    - Generate 60 items. (Items 51-60 will be used as backup buffer).

    ### NEWS DATA:
    {news_text[:25000]}
    """

    try:
        # High token limit for 60 questions
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        
        # Parse JSON
        quiz_data = json.loads(response.text)
        
        # Validation: Check count
        count = len(quiz_data)
        print(f"⚡ AI Generated {count} Questions.")
        
        if count < 10:
            print("⚠️ Warning: Low question count. News might be too short.")

        return quiz_data

    except Exception as e:
        print(f"❌ AI Error: {e}")
        return []

# --- 3. SAVE DATA ---
def save_quiz(data):
    if not data:
        print("⚠️ No data to save.")
        return

    # Shuffle Questions 1-50 (Keep 51-60 as buffer at end)
    # Strategy: Hum pure 60 save karenge, Frontend logic lagayega usage par.
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"💾 Saved {len(data)} High-Quality Questions to {OUTPUT_FILE}")

# --- EXECUTION ---
if __name__ == "__main__":
    news = fetch_news()
    if news:
        questions = generate_questions(news)
        save_quiz(questions)
