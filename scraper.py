import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import time

RSS_FEEDS = [
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",   
    "https://economictimes.indiatimes.com/rssfeeds/1898055.cms",    
    "https://www.thehindu.com/news/national/feeder/default.rss"    
]

KEYWORDS = [
    "RBI", "SEBI", "Bank", "Economy", "Scheme", "Yojana", "DRDO", "ISRO",
    "Summit", "MoU", "Agreement", "Award", "Appointment", "Resigns",
    "GDP", "Inflation", "Repo Rate", "Census", "Election", "Budget", 
    "Cabinet", "Minister", "Launch", "Inaugurate", "Exercise", "Military"
]

def scrape_feeds():
    news_items = []
    print("News dhoond raha hoon...")
    
    for feed_url in RSS_FEEDS:
        try:
            response = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all("item")
            
            for item in items:
                title = item.title.text.strip()
                link = item.link.text.strip()
                pub_date = item.pubDate.text.strip() if item.pubDate else str(datetime.date.today())
                
                if any(k.lower() in title.lower() for k in KEYWORDS):
                    news_items.append({
                        "title": title,
                        "link": link,
                        "date": pub_date,
                        "fetched_at": str(datetime.datetime.now())
                    })
        except Exception as e:
            print(f"Error scraping {feed_url}: {e}")
            
    return news_items

def process_files(new_data):
    
    print("Step 1: Saving to 1.json...")
    with open("1.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    
    if not new_data:
        print("Koi nayi news nahi mili aaj. Process stopped.")
        return

    
    print("Success! Waiting 30 seconds before processing next files...")
    time.sleep(30)

  
    if os.path.exists("2.json"):
        print("Step 3: Archiving old news from 2.json to All.txt...")
        try:
            with open("2.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
            
            
            with open("All.txt", "a", encoding="utf-8") as txt_file:
                for news in old_data:
                    
                    entry = f"[{news['date']}] {news['title']} \nLink: {news['link']}\n-------------------\n"
                    txt_file.write(entry)
        except Exception as e:
            print(f"Error archiving to All.txt: {e}")
    else:
        print("2.json pehle se nahi thi, isliye archive skip kiya.")

    
    print("Step 4: Updating 2.json with latest news...")
    with open("2.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    print("PROCESS COMPLETE: 1.json -> Wait -> All.txt Updated -> 2.json Updated.")

if __name__ == "__main__":
    found_news = scrape_feeds()
    process_files(found_news)
