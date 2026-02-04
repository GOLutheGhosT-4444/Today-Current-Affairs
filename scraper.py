import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import time
import re


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

def clean_text(text):
    
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_article_content(url):
    """Link par jakar poori news nikalta hai"""
    try:
        
        time.sleep(0.5) 
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=15) 
        soup = BeautifulSoup(response.content, 'html.parser')
        
        
        paragraphs = soup.find_all('p')
        
        full_text = ""
        for p in paragraphs:
            text = p.get_text().strip()
            
            if len(text) > 60: 
                full_text += text + " "
        
        return clean_text(full_text)
    except Exception as e:
        print(f"Failed to fetch content for {url}: {e}")
        return ""

def scrape_feeds():
    news_items = []
    print("Scanning ALL headlines from feeds...")
    
    for feed_url in RSS_FEEDS:
        try:
            print(f"Checking Feed: {feed_url}")
            response = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all("item")
            
            
            for item in items: 
                title = item.title.text.strip()
                link = item.link.text.strip()
                pub_date = item.pubDate.text.strip() if item.pubDate else str(datetime.date.today())
                
                
                if any(k.lower() in title.lower() for k in KEYWORDS):
                    
                    if any(existing['link'] == link for existing in news_items):
                        continue

                    print(f"Found Match: {title}")
                    
            
                    full_content = fetch_article_content(link)
                    
                    
                    if len(full_content) > 150:
                        news_items.append({
                            "title": title,
                            "content": full_content, 
                            "link": link,
                            "date": pub_date,
                            "fetched_at": str(datetime.datetime.now())
                        })
                        
        except Exception as e:
            print(f"Error scraping feed {feed_url}: {e}")
            
    return news_items

def process_files(new_data):
    
    print(f"Total relevant articles extracted: {len(new_data)}")
    
    with open("1.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    if not new_data:
        print("No new data found today.")
        return

    
    if os.path.exists("2.json"):
        try:
            with open("2.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
            
            
            with open("All.txt", "a", encoding="utf-8") as txt_file:
                for news in old_data:
                    entry = f"HEADLINE: {news['title']}\nDATE: {news['date']}\nCONTENT: {news['content']}\nLink: {news['link']}\n-------------------\n"
                    txt_file.write(entry)
            print("Archived old news to All.txt")
        except Exception as e:
            print(f"Archive error: {e}")

    
    with open("2.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    print("Done! Files updated.")

if __name__ == "__main__":
    found_news = scrape_feeds()
    process_files(found_news)
