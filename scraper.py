import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import time
import re

# --- CONFIGURATION ---
RSS_FEEDS = [
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",   # TOI India
    "https://economictimes.indiatimes.com/rssfeeds/1898055.cms",    # ET Markets
    "https://www.thehindu.com/news/national/feeder/default.rss"     # The Hindu
]

KEYWORDS = [
    "RBI", "SEBI", "Bank", "Economy", "Scheme", "Yojana", "DRDO", "ISRO",
    "Summit", "MoU", "Agreement", "Award", "Appointment", "Resigns",
    "GDP", "Inflation", "Repo Rate", "Census", "Election", "Budget", 
    "Cabinet", "Minister", "Launch", "Inaugurate", "Exercise", "Military"
]

def clean_text(text):
    # Text ko typing ke liye clean banana
    text = re.sub(r'\s+', ' ', text).strip() # Extra spaces hatana
    text = re.sub(r'\[.*?\]', '', text)      # [Cite] wagera hatana
    return text

def fetch_article_content(url):
    """Link par jakar poori news nikalta hai"""
    try:
        # Thoda wait karte hain taaki server block na kare
        time.sleep(1) 
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Logic: Page ke saare paragraphs (<p>) dhundo
        paragraphs = soup.find_all('p')
        
        full_text = ""
        for p in paragraphs:
            text = p.get_text().strip()
            # Sirf bade sentences uthao (ads aur captions avoid karne ke liye)
            if len(text) > 60: 
                full_text += text + " "
        
        return clean_text(full_text)
    except Exception as e:
        print(f"Failed to fetch content for {url}: {e}")
        return "Content not available."

def scrape_feeds():
    news_items = []
    print("Finding relevant news...")
    
    for feed_url in RSS_FEEDS:
        try:
            response = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all("item")
            
            # Limit: Har feed se sirf top 5 news check karenge (taaki process fast rahe)
            for item in items[:5]: 
                title = item.title.text.strip()
                link = item.link.text.strip()
                pub_date = item.pubDate.text.strip() if item.pubDate else str(datetime.date.today())
                
                # Check Keywords
                if any(k.lower() in title.lower() for k in KEYWORDS):
                    print(f"Fetching full text for: {title}")
                    
                    # YAHAN MAGIC HOTA HAI: Link khol kar pura text la raha hai
                    full_content = fetch_article_content(link)
                    
                    # Agar content 200 words se kam hai to typing ke liye bekar hai, skip karo
                    if len(full_content) > 200:
                        news_items.append({
                            "title": title,
                            "content": full_content, # Ye aap typing test me use karenge
                            "link": link,
                            "date": pub_date,
                            "fetched_at": str(datetime.datetime.now())
                        })
        except Exception as e:
            print(f"Error scraping feed {feed_url}: {e}")
            
    return news_items

def process_files(new_data):
    # --- 1.json (Temp) ---
    print(f"Found {len(new_data)} articles with full text.")
    with open("1.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    if not new_data:
        return

    time.sleep(5) # Thoda wait

    # --- Archive to All.txt ---
    if os.path.exists("2.json"):
        try:
            with open("2.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
            
            with open("All.txt", "a", encoding="utf-8") as txt_file:
                for news in old_data:
                    # Text format: Headline -> Full Content
                    entry = f"HEADLINE: {news['title']}\nCONTENT: {news['content']}\n-------------------\n"
                    txt_file.write(entry)
        except Exception as e:
            print(f"Archive error: {e}")

    # --- Update 2.json ---
    with open("2.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    print("Done! Full articles saved.")

if __name__ == "__main__":
    found_news = scrape_feeds()
    process_files(found_news)
