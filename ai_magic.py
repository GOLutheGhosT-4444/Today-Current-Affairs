import json
import os
import time
import google.generativeai as genai
import sys

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")

def get_best_model():
    """Auto-detect the best available model using official SDK"""
    if not API_KEY:
        print("❌ CRITICAL ERROR: GEMINI_API_KEY not found!")
        sys.exit(1)

    genai.configure(api_key=API_KEY)
    
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        preferred_order = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        for pref in preferred_order:
            if pref in available_models:
                return pref
                
        return available_models[0] if available_models else None
    except Exception as e:
        print(f"❌ Error fetching models: {e}")
        return None

def summarize_with_ai(model_name, title, content):
    """AI se strictly 3 facts nikalwayega from CONTENT using JSON mode"""
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    Analyze the following news content and extract EXACTLY 3 most important facts for Banking/SSC exams.
    Ensure facts contain amounts, dates, names, or new rules if present.
    
    Output strictly as a JSON object with a single key 'bullets' containing a list of 3 strings.
    Example: {{"bullets": ["Fact 1", "Fact 2", "Fact 3"]}}

    News Title: {title}
    News Content: {content[:15000]}  # Token limit safety
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Native JSON Mode applied
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
            
            # Parse the JSON response
            result = json.loads(response.text)
            bullets = result.get('bullets', [])
            
            # Join array into bullet points for PWA UI
            if len(bullets) >= 3:
                formatted_summary = "\n".join([f"• {b}" for b in bullets[:3]])
                return formatted_summary
            else:
                return "Error: AI generated incomplete points."

        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str:
                print(f"   ⚠️ Quota Hit! Waiting 60s before retry {attempt+1}/{max_retries}...")
                time.sleep(60)
                continue
            else:
                return f"API ERROR: {str(e)[:50]}"

    return "Summary Failed (Quota Exceeded)"

def process_news():
    print("🚀 Step 3: AI Magic Starting (Slow Mode for Free Tier)...")

    if not os.path.exists("2.json"): 
        print("❌ '2.json' not found. Run cleaner first.")
        return

    with open("2.json", "r", encoding="utf-8") as f:
        try: 
            full_data = json.load(f)
        except json.JSONDecodeError: 
            print("❌ '2.json' is corrupted.")
            return

    latest_news = full_data[:10]  # First 10 news items
    processed_data = []

    best_model = get_best_model()
    if not best_model:
        print("❌ Error: No AI Model Available.")
        return
        
    print(f"🤖 Selected Model: {best_model}\n")

    for i, item in enumerate(latest_news):
        title = item.get('title', 'No Title')
        content = item.get('content', '') # Ab real content use hoga
        
        # Ab AI dono (title aur content) analyze karega
        ai_summary = summarize_with_ai(best_model, title, content)

        if "ERROR" not in ai_summary and "Failed" not in ai_summary:
            print(f"   ✅ [{i+1}] Done: {title[:40]}...")
            
            # Update item with AI summary and save
            item['content'] = ai_summary
            processed_data.append(item)
        else:
            print(f"   ❌ [{i+1}] Failed: {title[:40]}... (Reason: {ai_summary})")

        # Free tier limit management
        if i < len(latest_news) - 1:
            print("      ⏳ Cooling down (15s)...")
            time.sleep(15) 

    with open("3.json", "w", encoding="utf-8") as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)

    print(f"\n🎉 Success! Premium exam facts saved to 3.json.")

if __name__ == "__main__":
    process_news()