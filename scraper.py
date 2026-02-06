import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import time
import google.generativeai as genai

# --- SECURITY UPDATE ---
# Key ab code me nahi, GitHub Secrets se aayegi
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ Error: API Key nahi mili! Make sure GitHub Secrets set hai.")
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

def clean_with_ai(headline, raw_text):
    if not raw_text or len(raw_text) < 50: return None

    prompt = f"""
    You are a strict News Editor for a student exam portal.
    
    Task:
    1. Analyze the HEADLINE and RAW TEXT.
    2. Extract ONLY factual news directly related to the HEADLINE.
    3. REMOVE: All ads, 'Read more', 'Subscribe', 'Follow us', generic footers, and unrelated sidebar text.
    4. REWRITE: Summarize the key facts in 60-80 words in professional, clear English.
    5. SAFETY CHECK: If the RAW TEXT is just navigation links, login pages, or unrelated to the headline, return EXACTLY: REJECT.

    HEADLINE: {headline}
    RAW TEXT: {raw_text[:4000]}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        return None if "REJECT" in text else text
    except:
        return None

def fetch_article_content(url):
    try:
        time.sleep(1)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        paragraphs = soup.find_all('p')
        raw_text = "\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30])
        return raw_text
    except:
        return ""

def scrape_feeds():
    news_items = []
    print("🚀 Running AI Scraper on GitHub Cloud...")
    
    for feed_url in RSS_FEEDS:
        try:
            print(f"Scanning: {feed_url}")
            response = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all("item")
            
            for item in items:
                title = item.title.text.strip()
                link = item.link.text.strip()
                pub_date = item.pubDate.text.strip() if item.pubDate else str(datetime.date.today())
                
                if any(k.lower() in title.lower() for k in KEYWORDS):
                    # Duplicate check against current session list
                    if any(x['link'] == link for x in news_items): continue
                    
                    print(f"Analyzing: {title[:40]}...")
                    raw = fetch_article_content(link)
                    clean = clean_with_ai(title, raw)
                    
                    if clean:
                        print("✅ AI Approved.")
                        news_items.append({
                            "title": title, "content": clean, "link": link,
                            "date": pub_date, "fetched_at": str(datetime.datetime.now())
                        })
                        time.sleep(4) # Rate limit safety
                    else:
                        print("❌ AI Rejected.")
        except Exception as e:
            print(f"Feed Error: {e}")
            
    return news_items

def process_files(new_data):
    # Load Existing Data to avoid duplicates over days
    all_data = []
    if os.path.exists("2.json"):
        try:
            with open("2.json", "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except: pass
    
    # Filter: Only add if link doesn't exist in 2.json
    unique_new = [n for n in new_data if not any(old['link'] == n['link'] for old in all_data)]
    
    if unique_new:
        print(f"Adding {len(unique_new)} new articles.")
        
        # 1.json update (Latest Only)
        with open("1.json", "w", encoding="utf-8") as f:
            json.dump(unique_new, f, indent=4, ensure_ascii=False)
            
        # 2.json update (Archive - Append new at top)
        updated_all = unique_new + all_data
        with open("2.json", "w", encoding="utf-8") as f:
            json.dump(updated_all[:100], f, indent=4, ensure_ascii=False) # Keep only last 100
    else:
        print("No new unique articles found.")

if __name__ == "__main__":
    found_news = scrape_feeds()
    process_files(found_news)
