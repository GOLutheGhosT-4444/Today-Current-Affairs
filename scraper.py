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

# --- MANUAL CLEANER (Updated with your Junk Text) ---
class ManualCleaner:
    def __init__(self):
        # Yahan maine aapke bheje gaye saare faltu phrases add kar diye hain
        self.junk_phrases = [
            "The View From India", "Looking at World Affairs",
            "Science For All", "First Day First Show News",
            "Today's Cache", "Data Point Decoding", "Health Matters",
            "Click here to read", "Subscribe to our newsletter",
            "Follow us on", "Terms of Use", "Privacy Policy",
            "Advertisement", "Sponsored", "Read more", "Also Read",
            "Related News", "Morning Briefing", "Evening Digest",
            "All rights reserved", "Copyright", "Join our WhatsApp",
            # --- NEW JUNK ADDED BELOW ---
            "News and reviews from the world of cinema",
            "Your download of the top 5 technology stories",
            "The weekly newsletter from science writers",
            "Decoding the headlines with facts",
            "Ramya Kannan writes to you",
            "Books of the week, reviews",
            "Updated - February", "Updated - January", # Dates remove karne ke liye
            "excerpts, new titles and features"
        ]

    def is_clean_line(self, line):
        """Check karta hai ki line kaam ki hai ya kachra"""
        line_lower = line.lower()
        
        # Rule 1: Agar line me koi junk phrase hai -> Reject
        for phrase in self.junk_phrases:
            if phrase.lower() in line_lower:
                return False
        
        # Rule 2: Length Check (Boilerplate lines usually short hoti hain)
        if len(line) < 40 and "." not in line:
            return False
            
        return True

    def clean(self, text):
        if not text: return None
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and self.is_clean_line(line):
                cleaned_lines.append(line)
        
        if len(cleaned_lines) < 2: 
            return None
            
        return " ".join(cleaned_lines)

cleaner = ManualCleaner()

# --- SCRAPING FUNCTIONS ---

def fetch_article_content(url):
    try:
        time.sleep(1)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        paragraphs = soup.find_all('p')
        
        full_text = ""
        for p in paragraphs:
            text = p.get_text().strip()
            # Sirf lambi lines uthao, chhoti lines (dates/author) ko yahi rok do
            if len(text) > 40:
                full_text += text + "\n"
        
        return full_text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def scrape_feeds():
    news_items = []
    print("🚀 Starting Manual Scraper...")
    
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
                    if any(x['link'] == link for x in news_items): continue
                    
                    print(f"Found: {title[:40]}...")
                    
                    raw_content = fetch_article_content(link)
                    clean_content = cleaner.clean(raw_content)
                    
                    if clean_content:
                        # Extra Check: Content me headline ka koi word hai ya nahi?
                        title_words = set(re.findall(r'\w+', title.lower()))
                        body_words = set(re.findall(r'\w+', clean_content.lower()))
                        
                        # Kam se kam 2 words match hone chahiye, nahi to wo Footer hai
                        if len(title_words.intersection(body_words)) >= 2:
                            print("✅ Cleaned & Saved.")
                            news_items.append({
                                "title": title,
                                "content": clean_content,
                                "link": link,
                                "date": pub_date,
                                "fetched_at": str(datetime.datetime.now())
                            })
                        else:
                            print("❌ Rejected (Irrelevant content)")
                    else:
                        print("❌ Rejected (Junk/Empty)")
                        
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
    
    unique_new = [n for n in new_data if not any(old['link'] == n['link'] for old in all_data)]
    
    if unique_new:
        print(f"Adding {len(unique_new)} new articles.")
        
        with open("1.json", "w", encoding="utf-8") as f:
            json.dump(unique_new, f, indent=4, ensure_ascii=False)
            
        updated_all = unique_new + all_data
        with open("2.json", "w", encoding="utf-8") as f:
            json.dump(updated_all[:100], f, indent=4, ensure_ascii=False)
    else:
        print("No new articles found.")

if __name__ == "__main__":
    found_news = scrape_feeds()
    process_files(found_news)
