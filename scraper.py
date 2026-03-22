import json
import os
import datetime
import time
import trafilatura
import feedparser

# ✅ Best practice: Alag-alag category ke specific keywords taki "Loss" ya "Book" par kachra na aaye
EXAM_KEYWORDS = [
    # Economy & Banking
    "Quarterly Result", "Fiscal Deficit", "Direct Tax", "GST", "Forex Reserves", 
    "World Bank", "IMF", "RBI", "SEBI", "Repo Rate", "Inflation", "UPI", "NPCI",
    # Defence & Space (Crucial for competitive exams)
    "DRDO", "ISRO", "Military Exercise", "Naval Exercise", "Air Force", "Missile", 
    "Spacecraft", "Satellite", "Defence Ministry",
    # Govt Policies & National
    "Yojana", "Scheme", "Cabinet Approval", "MoU", "Bilateral Agreement", 
    "Supreme Court", "Election Commission", "GDP Growth",
    # Awards & Appointments
    "Appointed as", "Takes charge as", "Nobel Prize", "Sahitya Akademi"
]

RSS_FEEDS = [

    "https://www.livemint.com/rss/news",
    "https://www.business-standard.com/rss/latest-news",
    "https://www.thehindu.com/business/feeder/default.rss",
    "https://economictimes.indiatimes.com/rssfeeds/1898055.cms",
    
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "https://economictimes.indiatimes.com/rssfeeds/1898055.cms",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://www.news18.com/rss/india.xml"

]

HISTORY_FILE = "scraped_urls.json"

def load_history():
    """Pehle se scrape kiye gaye URLs ko load karta hai taki duplicates na aayen."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_history(history_set):
    """Scrape ho chuke URLs ko save karta hai."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history_set), f, indent=4)

def fetch_clean_article(url):
    """Trafilatura ka use karke sirf pure news text nikalta hai, ads/menus ignore karta hai."""
    try:
        time.sleep(0.5) # Server block se bachne ke liye delay
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            # include_comments=False se user comments aur extra links hatt jate hain
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            return text if text else ""
        return ""
    except Exception as e:
        print(f"⚠️ Error fetching: {url} | Issue: {e}")
        return ""

def run_scraper():
    scraped_history = load_history()
    new_articles = []
    today_date = datetime.date.today().strftime("%Y-%m-%d")
    
    print("🚀 Scraper Started: Fetching premium exam-oriented news...\n")
    
    for feed_url in RSS_FEEDS:
        print(f"📡 Scanning Feed: {feed_url}")
        # feedparser XML ko safely parse karta hai bina crash hue
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            
            # Agar news pehle hi scrape ho chuki hai, toh skip karo
            if link in scraped_history:
                continue
                
            # Check karo ki title me hamare exam keywords hain ya nahi
            if any(keyword.lower() in title.lower() for keyword in EXAM_KEYWORDS):
                clean_content = fetch_clean_article(link)
                
                # Sirf wahi article save karo jisme actual data ho (kam se kam 200 characters)
                if clean_content and len(clean_content) > 200:
                    new_articles.append({
                        "title": title,
                        "content": clean_content,
                        "link": link,
                        "date": today_date,
                    })
                    scraped_history.add(link) # URL ko history me daal do
                    print(f"✅ Saved: {title[:60]}...")

    # Data ko date-wise file me save karna (e.g., news_2026-03-22.json)
    if new_articles:
        output_filename = f"news_{today_date}.json"
        
        # Agar aaj ki file pehle se hai, toh usme append karo
        if os.path.exists(output_filename):
            with open(output_filename, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            new_articles = existing_data + new_articles
            
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(new_articles, f, indent=4, ensure_ascii=False)
            
        save_history(scraped_history)
        print(f"\n🎉 Success! {len(new_articles)} pure, exam-ready articles saved in '{output_filename}'.")
    else:
        print("\n🤷‍♂️ Koi nayi relevant news nahi mili. Sab up-to-date hai!")

if __name__ == "__main__":
    run_scraper()
