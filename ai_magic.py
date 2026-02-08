import json
import os
import time
import requests

# --- CONFIGURATION ---
# GitHub Secret se Key uthayega.
# Agar Key nahi mili, to ye None rahega aur niche Error dega.
API_KEY = os.environ.get("GEMINI_API_KEY")

def summarize_with_ai(headline):
    if not API_KEY:
        return "Error: API Key Missing in GitHub Secrets."

    # Google Gemini Flash Model (Fast & Free)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    Act as a news editor. Summarize this headline into strictly 3 short bullet points.
    Focus on facts, dates, and numbers.
    Headline: "{headline}"
    Output format:
    • Point 1
    • Point 2
    • Point 3
    """
    
    data = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # ✅ SUCCESS
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # ❌ ERROR (Debug Info)
        else:
            print(f"⚠️ API Error for '{headline[:15]}...': {response.status_code} - {response.text}")
            return "Summary not available (API Error)."
            
    except Exception as e:
        print(f"⚠️ Connection Error: {e}")
        return "Summary not available (Connection Failed)."

def process_news():
    print("🚀 Step 3: AI Magic Starting...")
    
    # 1. Read Archive (2.json)
    if not os.path.exists("2.json"):
        print("❌ Error: 2.json nahi mila. Pehle scraper.py aur cut.py chalayein.")
        return

    with open("2.json", "r", encoding="utf-8") as f:
        try:
            full_data = json.load(f)
        except:
            print("❌ 2.json corrupted hai.")
            return

    # Sirf Latest 15 News process karenge (Quota bachane ke liye)
    latest_news = full_data[:15] 
    processed_data = []
    
    print(f"🤖 Processing top {len(latest_news)} headlines...")
    
    for i, item in enumerate(latest_news):
        headline = item.get('title', 'No Title')
        
        # AI Call
        ai_summary = summarize_with_ai(headline)
        
        # Console me status dikhao
        if "Error" not in ai_summary:
            print(f"   ✅ [{i+1}] Done: {headline[:30]}...")
        else:
            print(f"   ❌ [{i+1}] Failed: {headline[:30]}...")

        new_entry = {
            "title": headline,
            "content": ai_summary,
            "link": item.get('link', '#'),
            "date": item.get('date', 'Today')
        }
        processed_data.append(new_entry)
        
        # 2 Second ka break taaki Google block na kare
        time.sleep(2) 

    # 3. Save to 3.json
    with open("3.json", "w", encoding="utf-8") as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Success! Data saved to 3.json.")

if __name__ == "__main__":
    process_news()
