import json
import os
import time
import requests

# GitHub Secret se Key uthayega
API_KEY = os.environ.get("GEMINI_API_KEY")

def summarize_with_ai(headline):
    # Check 1: Kya Key load hui?
    if not API_KEY:
        return "CRITICAL ERROR: API Key missing in GitHub Secrets."

    # CHANGE: Hum 'gemini-1.5-flash' ki jagah 'gemini-pro' use kar rahe hain
    # Ye model purana hai lekin sabse stable hai (No 404 Errors)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"Summarize this news headline in 3 bullet points: '{headline}'"
    
    data = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # ✅ SUCCESS
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # ❌ ERROR (Abhi bhi error aaya to details print karega)
        else:
            error_details = response.text
            print(f"⚠️ API Error: {error_details}")
            return f"GOOGLE ERROR {response.status_code}: {error_details}"
            
    except Exception as e:
        return f"CONNECTION ERROR: {str(e)}"

def process_news():
    print("🚀 Step 3: AI Magic Starting (Using Stable Gemini-Pro)...")
    
    if not os.path.exists("2.json"):
        print("❌ Error: 2.json nahi mila.")
        return

    with open("2.json", "r", encoding="utf-8") as f:
        try: full_data = json.load(f)
        except: return

    # Sirf top 10 headlines process karenge
    latest_news = full_data[:10] 
    processed_data = []
    
    print(f"🤖 Processing top {len(latest_news)} headlines...")
    
    for i, item in enumerate(latest_news):
        headline = item.get('title', 'No Title')
        
        # AI Call
        ai_summary = summarize_with_ai(headline)
        
        # Console Log
        if "ERROR" not in ai_summary:
            print(f"   ✅ [{i+1}] Summary generated: {headline[:20]}...")
        else:
            print(f"   ❌ [{i+1}] Failed: {headline[:20]}...")

        new_entry = {
            "title": headline,
            "content": ai_summary, 
            "link": item.get('link', '#'),
            "date": item.get('date', 'Today')
        }
        processed_data.append(new_entry)
        time.sleep(1.5) 

    # Save to 3.json
    with open("3.json", "w", encoding="utf-8") as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)
        
    print(f"✅ AI Processing Complete. Data saved to 3.json.")

if __name__ == "__main__":
    process_news()
