import json
import os
import time
import google.generativeai as genai

# --- CONFIGURATION ---
# Yahan apni API Key dalein
API_KEY = "YOUR_GEMINI_API_KEY"

# Configure Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Flash model fast aur free hai

def summarize_with_ai(headline, content):
    try:
        # Prompt engineering: Hum AI ko bata rahe hain ki wo ek Teacher hai
        prompt = f"""
        Act as an expert Current Affairs teacher for competitive exams (UPSC, SSC, Banking).
        Summarize the following news into strictly 3 short bullet points.
        Focus ONLY on: Who, What, Where, Schemes, Dates, or numbers.
        Remove all political drama, opinions, and filler text.
        
        Headline: {headline}
        News: {content}
        
        Output format:
        • Point 1
        • Point 2
        • Point 3
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return content[:300] + "..." # Agar AI fail ho, to purana text use karo

def process_news():
    print("Step 3: AI Magic Starting... (Making news exam-ready)")
    
    # 1. Load Clean Data (From cut.py output)
    if not os.path.exists("1.json"):
        print("❌ Error: 1.json nahi mila.")
        return

    with open("1.json", "r", encoding="utf-8") as f:
        news_list = json.load(f)
    
    ai_processed_list = []
    
    # 2. Process Each Article
    print(f"🤖 Processing {len(news_list)} articles with Gemini AI...")
    
    for i, item in enumerate(news_list):
        print(f"   Writing Summary for: {item['title'][:30]}...")
        
        # AI ko call karo
        short_summary = summarize_with_ai(item['title'], item['content'])
        
        # Data Update karo
        item['content'] = short_summary
        ai_processed_list.append(item)
        
        # Thoda wait karo taaki Google ban na kare (Rate Limiting)
        time.sleep(2)

    # 3. Save Back to 1.json (Website ke liye)
    with open("1.json", "w", encoding="utf-8") as f:
        json.dump(ai_processed_list, f, indent=4, ensure_ascii=False)
    print("✅ 1.json updated with AI Summaries.")

    # 4. Update Archive (2.json)
    all_archive_data = []
    if os.path.exists("2.json"):
        try:
            with open("2.json", "r", encoding="utf-8") as f:
                all_archive_data = json.load(f)
        except: pass
        
    # Check duplicates and add new
    new_entries = []
    for news in ai_processed_list:
        if not any(old.get('link') == news['link'] for old in all_archive_data):
            new_entries.append(news)
            
    final_archive = new_entries + all_archive_data
    with open("2.json", "w", encoding="utf-8") as f:
        json.dump(final_archive[:100], f, indent=4, ensure_ascii=False)

    # 5. Generate all.txt (Clean & Short for Students)
    with open("all.txt", "w", encoding="utf-8") as f:
        if not ai_processed_list:
            f.write("No news for today.")
        else:
            for news in ai_processed_list:
                f.write(f"{'='*40}\n")
                f.write(f"🛑 {news['title']}\n") # Headline
                f.write(f"{'-'*20}\n")
                f.write(f"{news['content']}\n") # AI Summary (Bullet points)
                f.write(f"\nSource: {news['link']}\n")
                f.write(f"{'='*40}\n\n")

    print(f"✅ all.txt updated. AI processing complete!")

if __name__ == "__main__":
    process_news()