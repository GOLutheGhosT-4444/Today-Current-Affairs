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

# --- STRICT CLEANER ---
class ManualCleaner:
    def __init__(self):
        # IN PHRASES KO STRICTLY BAN KIYA GAYA HAI
        self.junk_phrases = [
            "News and reviews from the world of cinema",
            "Your download of the top 5 technology stories",
            "The weekly newsletter from science writers",
            "Decoding the headlines with facts",
            "Ramya Kannan writes to you",
            "getting to good health, and staying there",
            "Books of the week, reviews, excerpts",
            "Looking at World Affairs from the Indian perspective",
            "takes the jargon out of science",
            "puts the fun in!",
            "new titles and features",
            "The View From India", 
            "Science For All", 
            "Today's Cache", 
            "Data Point Decoding", 
            "Health Matters",
            "Click here to read", 
            "Subscribe to our newsletter",
            "Follow us on", 
            "Terms of Use", "Privacy Policy", "Advertisement", "Sponsored", 
            "Read more", "Also Read", "Related News", "Morning Briefing", 
            "Evening Digest", "All rights reserved", "Copyright", "Join our WhatsApp"
        ]

    def is_clean_line(self, line):
        """Line ko check karta hai"""
        line_lower = line.lower()
        
        # Rule 1: Date Pattern Removal (Published - February 06...)
        # Ye regex specifically us format ko pakadta hai jo aapne bheja
        if re.search(r'(published|updated)\s*-\s*[a-zA-Z]+\s+\d{1,2}', line_lower):
            return False

        # Rule 2: Strict Phrase Match
        # Agar line me upar wala koi bhi phrase mila, to poori line delete
        for phrase in self.junk_phrases:
            if phrase.lower() in line_lower:
                return False
        
        # Rule 3: Length Check (Chhoti lines bina full stop ke -> Menu items)
        if len(line) < 50 and "." not in line:
            return False
            
        return True

    def clean(self, text):
        if not text: return None
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Khali line skip karo
            if not line: continue
            
            # Filter check
            if self.is_clean_line(line):
                cleaned_lines.append(line)
        
        # Agar safai ke baad content bahut kam bacha (e.g. < 2 lines), to reject karo
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
        
        # Sirf main article body target karne ki koshish
        paragraphs = soup.find_all('p')
        
        full_text = ""
        for p in paragraphs:
            text = p.get_text().strip()
            
            # Filter 1: Sirf wahi lines uthao jo thodi lambi ho (40+ chars)
            if len(text) > 40:
                full_text += text + "\n"
        
        return full_text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def scrape_feeds():
    news_items = []
    print("🚀 Starting STRICT Manual Scraper...")
    
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
                    # Duplicate check current session
                    if any(x['link'] == link for x in news_items): continue
                    
                    print(f"Found: {title[:40]}...")
                    
                    # 1. Fetch Raw
                    raw_content = fetch_article_content(link)
                    
                    # 2. Deep Clean
                    clean_content = cleaner.clean(raw_content)
                    
                    if clean_content:
                        # 3. Relevance Check (Headline match)
                        title_words = set(re.findall(r'\w+', title.lower()))
                        body_words = set(re.findall(r'\w+', clean_content.lower()))
                        
                        # Headline ke 2 words body me hone chahiye
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
                            print("❌ Rejected (Content mismatch/Footer detected)")
                    else:
                        print("❌ Rejected (Empty/Junk)")
                        
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
    
    # Filter Unique (Link check against 2.json)
    unique_new = [n for n in new_data if not any(old['link'] == n['link'] for old in all_data)]
    
    if unique_new:
        print(f"Adding {len(unique_new)} new articles.")
        
        # Save 1.json
        with open("1.json", "w", encoding="utf-8") as f:
            json.dump(unique_new, f, indent=4, ensure_ascii=False)
            
        # Save 2.json
        updated_all = unique_new + all_data
        with open("2.json", "w", encoding="utf-8") as f:
            json.dump(updated_all[:100], f, indent=4, ensure_ascii=False)
    else:
        print("No new articles found.")

if __name__ == "__main__":
    found_news = scrape_feeds()
    process_files(found_news)
