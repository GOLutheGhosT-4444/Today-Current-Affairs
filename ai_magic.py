import json
import os
import time
import requests

# --- CONFIGURATION ---
# GitHub Secret se Key uthayega, ya manually yahan dalein
API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

def summarize_with_ai(headline):
    # Sirf Headline bhejenge taaki AI uske base par facts nikale
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    Act as a strictly professional news editor.
    I will give you a news HEADLINE. 
    You have to generate a short summary (strictly 3 bullet points) explaining that news.
    Focus on: What happened? Who is involved? Any important numbers/dates?
    
    Headline: "{headline}"
    
    Output format:
    • Point 1
    • Point 2
    • Point 3
    (Keep it extremely short and exam-oriented)
    """
    
    data = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            return "Summary not available due to API error."
    except:
        return "Summary not available."

def process_news():
    print("🚀 Step 3: AI Magic Starting (Target: 3.json)...")
    
    # 1. Read Archive (2.json) - SIRF READ MODE MEIN
    if not os.path.exists("2.json"):
        print("❌ Error: 2.json nahi mila.")
        return

    with open("2.json", "r", encoding="utf-8") as f:
        try:
            full_data = json.load(f)
        except:
            print("❌ 2.json corrupted hai.")
            return

    # 2. Select Latest News only
    # Hum sirf top 20 news lenge taaki API limit khatam na ho
    latest_news = full_data[:20] 
    
    processed_data = []
    
    print(f"🤖 Processing latest {len(latest_news)} headlines from 2.json...")
    
    for i, item in enumerate(latest_news):
        headline = item.get('title', 'No Title')
        print(f"   [{i+1}] Summarizing: {headline[:40]}...")
        
        # AI se kaho: Sirf Headline dekho aur summary banao
        ai_summary = summarize_with_ai(headline)
        
        # Naya object banao (Purana data kharab nahi karna)
        new_entry = {
            "title": headline,
            "content": ai_summary,  # Yahan AI ki summary aayegi
            "link": item.get('link', '#'),
            "date": item.get('date', 'Today')
        }
        
        processed_data.append(new_entry)
        time.sleep(1.5) # Thoda saans lene do script ko

    # 3. Save to NEW File (3.json)
    # 1.json aur 2.json ko haath bhi nahi lagaya jayega
    with open("3.json", "w", encoding="utf-8") as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Success! Data saved to 3.json. (1.json & 2.json are safe)")

if __name__ == "__main__":
    process_news()