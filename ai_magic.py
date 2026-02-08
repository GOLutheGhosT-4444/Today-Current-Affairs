import json
import os
import time
import requests

# GitHub Secret se Key uthayega
API_KEY = os.environ.get("GEMINI_API_KEY")

# Global variable to store the working model name
CURRENT_MODEL = None

def get_best_model():
    """Google se poocho ki kaunsa model zinda hai"""
    global CURRENT_MODEL
    
    if not API_KEY:
        print("❌ Error: API Key missing.")
        return None

    # Step 1: List all available models
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Failed to list models: {response.text}")
            return None
            
        data = response.json()
        
        # Step 2: Find a model that supports 'generateContent'
        # Priority: Flash > Pro > Any
        preferred_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        available_models = []

        if 'models' in data:
            for m in data['models']:
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    # Model name usually looks like "models/gemini-1.5-flash"
                    clean_name = m['name'].replace('models/', '')
                    available_models.append(clean_name)

        # Step 3: Pick the best one
        for pref in preferred_models:
            if pref in available_models:
                print(f"✅ Selected Model: {pref}")
                return pref
        
        # Agar preferred nahi mila, to jo pehla mila wo le lo
        if available_models:
            print(f"⚠️ Preferred model not found. Using fallback: {available_models[0]}")
            return available_models[0]
            
        print("❌ No suitable text-generation model found.")
        return None

    except Exception as e:
        print(f"❌ Connection Error during model check: {e}")
        return None

def summarize_with_ai(headline):
    global CURRENT_MODEL
    
    # Agar model abhi tak select nahi hua, to pata karo
    if not CURRENT_MODEL:
        CURRENT_MODEL = get_best_model()
        if not CURRENT_MODEL:
            return "Error: No AI Model Available."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{CURRENT_MODEL}:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"Summarize this news headline in 3 bullet points: '{headline}'"
    
    data = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            return f"API ERROR {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"CONNECTION ERROR: {str(e)}"

def process_news():
    print("🚀 Step 3: AI Magic Starting (Auto-Model Mode)...")
    
    if not os.path.exists("2.json"):
        print("❌ Error: 2.json nahi mila.")
        return

    with open("2.json", "r", encoding="utf-8") as f:
        try: full_data = json.load(f)
        except: return

    # Sirf top 10 headlines process karenge
    latest_news = full_data[:10] 
    processed_data = []
    
    # Pehle model check kar lo taaki loop me baar baar check na karna pade
    global CURRENT_MODEL
    CURRENT_MODEL = get_best_model()
    
    if not CURRENT_MODEL:
        print("❌ Critical: AI Model connect nahi ho pa raha.")
        return

    print(f"🤖 Processing top {len(latest_news)} headlines using {CURRENT_MODEL}...")
    
    for i, item in enumerate(latest_news):
        headline = item.get('title', 'No Title')
        
        ai_summary = summarize_with_ai(headline)
        
        if "ERROR" not in ai_summary:
            print(f"   ✅ [{i+1}] Done: {headline[:20]}...")
        else:
            print(f"   ❌ [{i+1}] Failed: {ai_summary}")

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
        
    print(f"✅ Success! Data saved to 3.json.")

if __name__ == "__main__":
    process_news()
