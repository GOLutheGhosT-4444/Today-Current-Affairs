import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import time
import re

# --- CONFIGURATION: RELIABLE RSS FEEDS ---
RSS_FEEDS = [
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",   # TOI India
    "https://economictimes.indiatimes.com/rssfeeds/1898055.cms",    # ET Markets
    "https://www.thehindu.com/news/national/feeder/default.rss"     # The Hindu
]

# --- KEYWORDS FOR SSC/BANK EXAMS ---
KEYWORDS = [
    "RBI", "SEBI", "Bank", "Economy", "Scheme", "Yojana", "DRDO", "ISRO",
    "Summit", "MoU", "Agreement", "Award", "Appointment", "Resigns",
    "GDP", "Inflation", "Repo Rate", "Census", "Election", "Budget", 
    "Cabinet", "Minister", "Launch", "Inaugurate", "Exercise", "Military"
]

def clean_text(text):
    # Text ko typing practice ke liye clean banana
    text = re.sub(r'\s+', ' ', text).strip() # Extra spaces hatana
    return text

def fetch_article_content(url):
    """Link par jakar poori news nikalta hai (Full Body Text)"""
    try:
        # 1 second wait taaki server block na kare
        time.sleep(1) 
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Logic: Page ke saare paragraphs (<p>) dhundo
        paragraphs = soup.find_all('p')
        
        full_text = ""
        for p in paragraphs:
            text = p.get_text().strip()
            # Sirf meaningful lines uthao (Ads/Captions avoid karne ke liye > 60 chars)
            if len(text) > 60: 
                full_text += text + " "
        
        return clean_text(full_text)
    except Exception as e:
        print(f"Failed to fetch content for {url}: {e}")
        return ""

def scrape_feeds():
    news_items = []
    print("Finding relevant news...")
    
    for feed_url in RSS_FEEDS:
        try:
            response = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all("item")
            
            # Speed ke liye har feed se sirf Top 5 news check karenge
            for item in items[:5]: 
                title = item.title.text.strip()
                link = item.link.text.strip()
                pub_date = item.pubDate.text.strip() if item.pubDate else str(datetime.date.today())
                
                # Check Keywords
                if any(k.lower() in title.lower() for k in KEYWORDS):
                    print(f"Fetching full text for: {title}")
                    
                    # Link khol kar pura text la raha hai
                    full_content = fetch_article_content(link)
                    
                    # Agar content 200 characters se bada hai tabhi save karo
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
    # --- STEP 1: Save to 1.json (Temporary) ---
    print(f"Found {len(new_data)} articles with full text.")
    with open("1.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    if not new_data:
        print("No new data found. Stopping.")
        return

    # --- STEP 2: Archive Old Data to All.txt ---
    if os.path.exists("2.json"):
        try:
            with open("2.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
            
            with open("All.txt", "a", encoding="utf-8") as txt_file:
                for news in old_data:
                    # Text format: Headline -> Full Content
                    entry = f"HEADLINE: {news['title']}\nCONTENT: {news['content']}\nLink: {news['link']}\n-------------------\n"
                    txt_file.write(entry)
            print("Archived old news to All.txt")
        except Exception as e:
            print(f"Archive error: {e}")

    # --- STEP 3: Update 2.json ---
    with open("2.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    print("Done! 2.json updated with latest typing content.")

if __name__ == "__main__":
    found_news = scrape_feeds()
    process_files(found_news)
