import os
import json
import requests
import google.generativeai as genai
import random

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")
NEWS_SOURCE = "https://raw.githubusercontent.com/GOLutheGhosT-4444/Today-Current-Affairs/refs/heads/main/2.json"
OUTPUT_FILE = "quiz.json"

# --- BACKUP DATA (Agar AI Fail ho jaye to ye use hoga) ---
BACKUP_QUESTIONS = [
    {"q": "What is the current Repo Rate fixed by RBI?", "a": "6.50%", "options": ["6.25%", "6.50%", "6.75%", "6.00%", "6.35%"], "cat": "Banking"},
    {"q": "Who is the current Governor of RBI?", "a": "Shaktikanta Das", "options": ["Urjit Patel", "Raghuram Rajan", "Shaktikanta Das", "M.D. Patra", "Nirmala Sitharaman"], "cat": "Appointments"},
    {"q": "Where is the Headquarters of ISRO located?", "a": "Bengaluru", "options": ["Chennai", "Mumbai", "Bengaluru", "Delhi", "Hyderabad"], "cat": "Science"},
    {"q": "Which article of the Constitution deals with the Annual Financial Statement (Budget)?", "a": "Article 112", "options": ["Article 110", "Article 112", "Article 280", "Article 360", "Article 108"], "cat": "Polity"},
    {"q": "What is the full form of 'UPI' in digital payments?", "a": "Unified Payments Interface", "options": ["Unified Payments Interface", "Union Pay India", "Universal Payment ID", "United Payment Interface", "Unique Payment Identity"], "cat": "Banking"},
    {"q": "National Youth Day is celebrated on?", "a": "12 January", "options": ["12 January", "15 January", "10 January", "25 January", "28 February"], "cat": "Dates"},
    {"q": "Who is the Chairman of SEBI?", "a": "Madhabi Puri Buch", "options": ["Ajay Tyagi", "Madhabi Puri Buch", "U.K. Sinha", "Debasish Panda", "Ashish Chauhan"], "cat": "Appointments"},
    {"q": "What does 'G' stand for in 'GDP'?", "a": "Gross", "options": ["Growth", "Gross", "Global", "General", "Goods"], "cat": "Economy"},
    {"q": "Which is the largest Public Sector Bank in India?", "a": "State Bank of India", "options": ["Punjab National Bank", "Bank of Baroda", "State Bank of India", "Canara Bank", "Union Bank"], "cat": "Banking"},
    {"q": "When is 'World Environment Day' celebrated?", "a": "5 June", "options": ["5 June", "22 April", "16 September", "5 July", "1 May"], "cat": "Dates"}
]

def fetch_news():
    print("📥 Fetching News...")
    try:
        response = requests.get(NEWS_SOURCE)
        if response.status_code == 200:
            try:
                data = response.json()
                text_data = ""
                for item in data:
                    content = item.get('content', '') or item.get('summary', '')
                    if len(content) > 50:
                        text_data += f"- {content}\n"
                return text_data
            except:
                return response.text
    except Exception as e:
        print(f"❌ News Fetch Error: {e}")
    return None

def generate_questions(news_text):
    if not API_KEY:
        print("❌ API Key Missing. Using Backup.")
        return BACKUP_QUESTIONS

    if not news_text:
        print("❌ No News Data. Using Backup.")
        return BACKUP_QUESTIONS

    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are an Expert Exam Setter for IBPS/SBI PO.
    Create exactly 50 High-Level One-Liner MCQs from this news.
    
    CRITERIA:
    1. Categories: Amount, Who, Where, When, Why.
    2. Options: 5 options (1 correct, 4 confusing).
    3. Output: RAW JSON Array only. No markdown.
    4. Structure: [{{"q": "...", "a": "...", "options": ["..."], "cat": "..."}}]
    
    NEWS:
    {news_text[:15000]}
    """

    try:
        print("🤖 Asking AI...")
        response = model.generate_content(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        if len(data) < 5:
            print("⚠️ AI generated too few questions. Mixing with Backup.")
            return data + BACKUP_QUESTIONS
            
        print(f"✅ AI Generated {len(data)} Questions.")
        return data

    except Exception as e:
        print(f"❌ AI Error: {e}")
        return BACKUP_QUESTIONS

def save_file(data):
    # Ensure data is never empty
    if not data:
        data = BACKUP_QUESTIONS
        
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"💾 Successfully saved {len(data)} questions to {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Critical Error Saving File: {e}")

if __name__ == "__main__":
    news = fetch_news()
    quiz_data = generate_questions(news)
    save_file(quiz_data)
