import requests
from bs4 import BeautifulSoup
import json
import datetime
import time

RSS_FEEDS = [
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "https://economictimes.indiatimes.com/rssfeeds/1898055.cms",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "https://www.news18.com/rss/india.xml"
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

def fetch_raw_content(url):
    try:
        time.sleep(0.5)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        paragraphs = soup.find_all('p')
        full_text = "\n".join([p.get_text().strip() for p in paragraphs])
        
        return full_text
    except Exception:
        return ""

def run_scraper():
    raw_news = []
    print("Step 1: Fetching Raw News...")
    
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
                    content = fetch_raw_content(link)
                    
                    if len(content) > 50: 
                        raw_news.append({
                            "title": title,
                            "content": content,
                            "link": link,
                            "date": pub_date,
                            "fetched_at": str(datetime.datetime.now())
                        })
        except Exception as e:
            print(f"Error: {e}")
    with open("1.json", "w", encoding="utf-8") as f:
        json.dump(raw_news, f, indent=4, ensure_ascii=False)
    print(f"✅ Step 1 Complete: {len(raw_news)} raw articles saved.")

if __name__ == "__main__":
    run_scraper()
