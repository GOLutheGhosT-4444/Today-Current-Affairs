import json
import os
import time
import requests


API_KEY = os.environ.get("GEMINI_API_KEY")

CURRENT_MODEL = None

def get_best_model():
    """Google se poocho ki kaunsa model zinda hai"""
    global CURRENT_MODEL
    if not API_KEY: return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        
        
        preferred_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        available_models = []

        if 'models' in data:
            for m in data['models']:
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    clean_name = m['name'].replace('models/', '')
                    available_models.append(clean_name)

        for pref in preferred_models:
            if pref in available_models:
                return pref
        
        return available_models[0] if available_models else None
    except:
        return None

def summarize_with_ai(headline):
    global CURRENT_MODEL
    if not CURRENT_MODEL:
        CURRENT_MODEL = get_best_model()
        if not CURRENT_MODEL: return "Error: No AI Model Available."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{CURRENT_MODEL}:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt_text = f"Summarize this news headline in 3 bullet points: '{headline}'"
    data = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data)
            
        
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            
            
            elif response.status_code == 429:
                print(f"   ⚠️ Quota Hit! Waiting 60s before retry {attempt+1}/{max_retries}...")
                time.sleep(60)
                continue
            
        
            else:
                return f"API ERROR {response.status_code}: {response.text}"
                
        except Exception as e:
            time.sleep(5)
            continue

    return "Summary Failed (Quota Exceeded)"

def process_news():
    print("🚀 Step 3: AI Magic Starting (Slow Mode for Free Tier)...")
    
    if not os.path.exists("2.json"): return

    with open("2.json", "r", encoding="utf-8") as f:
        try: full_data = json.load(f)
        except: return

    
    latest_news = full_data[:10] 
    processed_data = []
    
    global CURRENT_MODEL
    CURRENT_MODEL = get_best_model()
    print(f"🤖 Model: {CURRENT_MODEL}")
    
    for i, item in enumerate(latest_news):
        headline = item.get('title', 'No Title')
        
        ai_summary = summarize_with_ai(headline)
        
        if "ERROR" not in ai_summary and "Failed" not in ai_summary:
            print(f"   ✅ [{i+1}] Done: {headline[:20]}...")
        else:
            print(f"   ❌ [{i+1}] Failed: {headline[:20]}...")

        new_entry = {
            "title": headline,
            "content": ai_summary,
            "link": item.get('link', '#'),
            "date": item.get('date', 'Today')
        }
        processed_data.append(new_entry)
        
    
        print("      ⏳ Cooling down (15s)...")
        time.sleep(15) 

    with open("3.json", "w", encoding="utf-8") as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Success! Data saved to 3.json.")

if __name__ == "__main__":
    process_news()
