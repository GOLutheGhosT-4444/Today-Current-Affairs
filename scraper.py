import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import time
import re
import string  # Naya Import: Punctuation hatane ke liye

# --- 1. CONFIGURATION ---
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

# --- 2. THE CLEANER CLASS (INTEGRATED) ---
class UniversalNewsCleaner:
    def __init__(self):
        # 1. Junk Phrases List (Har site ke common ads/links)
        self.junk_patterns = [
            r"follow us on", r"share this article", r"join our whatsapp", 
            r"click here to", r"subscribe to", r"sign up for", 
            r"like us on", r"twitter", r"facebook", r"instagram",
            r"advertisement", r"sponsored", r"read more", r"also read", 
            r"related news", r"watch video", r"photo gallery",
            r"all rights reserved", r"copyright", r"terms of use", 
            r"privacy policy", r"disclaimer", r"contact us",
            r"morning briefing", r"evening digest", r"todays top stories",
            r"loading\.\.\.", r"please wait", r"the view from india", 
            r"science for all", r"today's cache", r"data point decoding"
        ]

        # 2. Stopwords (Relevance check ke liye)
        self.stopwords = {
            'is', 'am', 'are', 'was', 'were', 'the', 'a', 'an', 'and', 'but', 'or', 
            'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'this', 'that',
            'it', 'he', 'she', 'they', 'we', 'you', 'his', 'her', 'their', 'has', 'have'
        }

    def _clean_text_basic(self, text):
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _is_junk_line(self, line):
        line_lower = line.lower()
        # Rule: Agar line 30 chars se chhoti hai aur Full stop nahi hai, to wo menu/link hai
        if len(line) < 30 and "." not in line:
            return True
        # Rule: Junk Patterns
        for pattern in self.junk_patterns:
            if re.search(pattern, line_lower):
                return True
        return False

    def _get_significant_words(self, text):
        # Punctuation hatana aur words nikalna
        text = text.lower().translate(str.maketrans('', '', string.punctuation))
        words = set(text.split())
        return words - self.stopwords

    def clean_and_validate(self, headline, raw_text):
        if not raw_text or not headline:
            return None

        lines = raw_text.split('\n')
        cleaned_lines = []

        # Step 1: Line Filtering
        for line in lines:
            line = self._clean_text_basic(line)
            if not line: continue
            
            if not self._is_junk_line(line):
                cleaned_lines.append(line)

        if len(cleaned_lines) == 0:
            return None

        final_body = " ".join(cleaned_lines)

        # Step 2: Relevance Check (Headline Match)
        headline_words = self._get_significant_words(headline)
        body_words = self._get_significant_words(final_body)
        
        common_count = len(headline_words.intersection(body_words))

        # Agar body me headline ke words nahi mile, to ye junk hai
        if common_count < 2:
            # Exception: Agar article breaking news hai (chhota hai), to 1 match bhi chalega
            if len(final_body) < 300 and common_count >= 1:
                return final_body
            return None # REJECTED

        return final_body

# Initialize Cleaner
cleaner = UniversalNewsCleaner()


# --- 3. SCRAPING FUNCTIONS ---

def fetch_article_content(url):
    """
    Link se raw paragraphs nikalta hai.
    NOTE: Ab hum text ko '\n' se jodenge taaki cleaner line-by-line check kar sake.
    """
    try:
        time.sleep(0.5) 
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=15) 
        soup = BeautifulSoup(response.content, 'html.parser')
        
        paragraphs = soup.find_all('p')
        
        raw_lines = []
        for p in paragraphs:
            text = p.get_text().strip()
            # Yahan loose filter rakhenge, strict filter 'Cleaner' karega
            if len(text) > 20: 
                raw_lines.append(text)
        
        # Join with New Line for processing
        return "\n".join(raw_lines)

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
                
                # 1. Check Keyword Match
                if any(k.lower() in title.lower() for k in KEYWORDS):
                    
                    if any(existing['link'] == link for existing in news_items):
                        continue

                    print(f"Checking Article: {title}")
            
                    # 2. Fetch Raw Content
                    raw_content = fetch_article_content(link)
                    
                    # 3. CLEAN & VALIDATE (The Magic Step)
                    final_content = cleaner.clean_and_validate(title, raw_content)
                    
                    if final_content:
                        print(f"✅ Accepted: {title[:30]}...")
                        news_items.append({
                            "title": title,
                            "content": final_content, # Cleaned text save hoga
                            "link": link,
                            "date": pub_date,
                            "fetched_at": str(datetime.datetime.now())
                        })
                    else:
                        print(f"❌ Rejected (Junk/Irrelevant): {title[:30]}...")
                        
        except Exception as e:
            print(f"Error scraping feed {feed_url}: {e}")
            
    return news_items

def process_files(new_data):
    print(f"Total VALID articles saved: {len(new_data)}")
    
    # Save Latest
    with open("1.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    if not new_data:
        print("No new valid data found today.")
        return

    # Archive Logic
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

    # Update Daily File
    with open("2.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    print("Done! Files updated.")

if __name__ == "__main__":
    found_news = scrape_feeds()
    process_files(found_news)
