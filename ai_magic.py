import json
import os
import time
import requests

# GitHub Secret se Key uthayega
API_KEY = os.environ.get("GEMINI_API_KEY")

def summarize_with_ai(headline):
    # Check 1: Kya Key load hui?
    if not API_KEY:
        return "CRITICAL ERROR: API Key script tak nahi pahunchi. GitHub Secrets check karein."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"Summarize this news headline in 3 bullet points: '{headline}'"
    
    data = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # ✅ SUCCESS
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # ❌ ERROR (Detective Mode: Asli reason batao)
        else:
            # Google ka pura error message capture karo
            error_details = response.text
            print(f"⚠️ API Error: {error_details}") # Logs ke liye
            
            # JSON me error save karo taaki hum padh sakein
            return f"GOOGLE ERROR {response.status_code}: {error_details}"
            
    except Exception as e:
        return f"CONNECTION ERROR: {str(e)}"

def process_news():
    print("🚀 Step 3: AI Magic Starting...")
    
    if not os.path.exists("2.json"):
        print("❌ Error: 2.json nahi mila.")
        return

    with open("2.json", "r", encoding="utf-8") as f:
        try: full_data = json.load(f)
        except: return

    # Sirf top 5 check karte hain testing ke liye
    latest_news = full_data[:5] 
    processed_data = []
    
    print(f"🤖 Processing top {len(latest_news)} headlines...")
    
    for item in latest_news:
        headline = item.get('title', 'No Title')
        
        # AI Call
        ai_summary = summarize_with_ai(headline)
        
        new_entry = {
            "title": headline,
            "content": ai_summary, # Yahan ab asli error likha aayega
            "link": item.get('link', '#'),
            "date": item.get('date', 'Today')
        }
        processed_data.append(new_entry)
        time.sleep(1) 

    # Save to 3.json
    with open("3.json", "w", encoding="utf-8") as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Debug Run Complete. Check 3.json for error details.")

if __name__ == "__main__":
    process_news()
