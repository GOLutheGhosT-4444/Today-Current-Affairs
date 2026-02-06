import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import time
import google.generativeai as genai

# --- SECURITY ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ Error: API Key nahi mili! GitHub Secrets check karein.")
    exit(1)

# --- CONFIGURATION ---
RSS_FEEDS = [
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",   # TOI India
    "https://economictimes.indiatimes.com/rssfeeds/1898055.cms",    # ET Markets
    "https://www.thehindu.com/news/national/feeder/default.rss",    # The Hindu National
    "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms", # TOI Business
    "https://www.news18.com/rss/india.xml"                          # News18 India
]

KEYWORDS = [
    "Quarterly Result", "Profit", "Loss", "Merger", "Acquisition", 
    "Penalty", "Fine", "Loan", "Credit", "Debit", "UPI", "NPCI", 
    "Fiscal Deficit", "Direct Tax", "GST", "Sensex", "Nifty", 
    "Forex", "Reserves", "USD", "Rupee", "IMF", "World Bank",
    "RBI", "SEBI", "Bank", "Economy", "Scheme", "Yojana", "DRDO", "ISRO",
    "Summit", "MoU", "Agreement", "Award", "Appointment", "Resigns",
    "GDP", "Inflation", "Repo Rate", "Census", "Election", "Budget", 
    "Cabinet", "Minister", "Launch", "Inaugurate", "Exercise", "Military",
    "Govt", "Government", "Policy", "Project", "Development", "Railway",
    "Sports", "Medal", "Tournament", "Championship", "Author", "Book"
]

# AI Setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 🆕 SPECIAL CLEANER FUNCTION ---
def remove_specific_junk(text):
    """
    Ye function specific The Hindu aur dusre sites ke footer/promo text ko hatata hai.
    """
    junk_phrases = [
        "Looking at World Affairs from the Indian perspective",
        "News and reviews from the world of cinema",
        "Your download of the top 5 technology stories",
        "The weekly newsletter from science writers",
        "Decoding the headlines with facts",
        "Ramya Kannan writes to you",
        "Books of the week",
        "Published -",
        "Updated -",
        "READ MORE",
        "SUBSCRIBE",
        "Follow us on"
    ]
    
    # Line by line check karke safai
    clean_lines = []
    lines = text.split('\n')
    for line in lines:
        is_junk = False
        for phrase in junk_phrases:
            if phrase.lower() in line.lower():
                is_junk = True
                break
        
        # Agar line bahut chhoti hai aur usme koi kaam ka content nahi, to hata do
        if not is_junk and len(line.strip()) > 5:
            clean_lines.append(line.strip())
            
    return "\n".join(clean_lines)

def generate_news_from_summary(headline, description):
    """
    AI Writer: RSS ki summary se Full Article banata hai.
    """
    # Step 1: Pehle Python se kachra saaf karo
    clean_description = remove_specific_junk(description)
    
    if not clean_description or len(clean_description) < 10:
        clean_description = "Details not available in feed."

    # Step 2: Ab AI ko bolo ki news banaye
    prompt = f"""
    You are a professional News Reporter.
    
    INPUT:
    Headline: {headline}
    Context: {clean_description}
    
    TASK:
    1. Write a short, crisp news summary (60-80 words).
    2. Focus ONLY on the main event mentioned in the Headline.
    3. IGNORE any text that looks like a newsletter promo, advertisement, or footer (e.g., "Looking at World Affairs...").
    4. Do NOT use phrases like "The article discusses" or "According to the source".
    
    OUTPUT: 
    Return only the clean news paragraph.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Double check: Agar AI ne galti se "Rejected" bola ho
        if "REJECT" in text: return None
        return text
    except:
        return None

def scrape_feeds():
    news_items = []
    print("🚀 AI News Generator Started (Smart Filter Mode)...")
    
    for feed_url in RSS_FEEDS:
        try:
            print(f"Reading Feed: {feed_url}")
            response = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all("item")
            
            for item in items:
                title = item.title.text.strip()
                link = item.link.text.strip()
                pub_date = item.pubDate.text.strip() if item.pubDate else str(datetime.date.today())
                
                # Description RSS se nikalna
                description = item.description.text.strip() if item.description else ""
                
                if any(k.lower() in title.lower() for k in KEYWORDS):
                    # Duplicate Check
                    if any(x['link'] == link for x in news_items): continue
                    
                    print(f"Generating: {title[:40]}...")
                    
                    # AI Generation Call
                    ai_content = generate_news_from_summary(title, description)
                    
                    if ai_content:
                        print("✅ Generated.")
                        news_items.append({
                            "title": title, 
                            "content": ai_content,
                            "link": link,
                            "date": pub_date, 
                            "fetched_at": str(datetime.datetime.now())
                        })
                        time.sleep(3) # Rate limit safety
                    else:
                        print("❌ AI Error or Rejected.")
        except Exception as e:
            print(f"Feed Error: {e}")
            
    return news_items

def process_files(new_data):
    all_data = []
    if os.path.exists("2.json"):
        try:
            with open("2.json", "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except: pass
    
    # Filter unique
    unique_new = [n for n in new_data if not any(old['link'] == n['link'] for old in all_data)]
    
    if unique_new:
        print(f"Adding {len(unique_new)} new AI-generated articles.")
        
        # Save Latest
        with open("1.json", "w", encoding="utf-8") as f:
            json.dump(unique_new, f, indent=4, ensure_ascii=False)
            
        # Archive
        updated_all = unique_new + all_data
        with open("2.json", "w", encoding="utf-8") as f:
            json.dump(updated_all[:100], f, indent=4, ensure_ascii=False)
    else:
        print("No new news found.")

if __name__ == "__main__":
    found_news = scrape_feeds()
    process_files(found_news)
