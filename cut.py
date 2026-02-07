import json
import os
import re

KILL_PHRASES = [
    "Looking at World Affairs from the Indian perspective",
    "News and reviews from the world of cinema",
    "Your download of the top 5 technology stories",
    "The weekly newsletter from science writers",
    "takes the jargon out of science",
    "Decoding the headlines with facts",
    "Ramya Kannan writes to you",
    "getting to good health, and staying there",
    "Books of the week, reviews, excerpts",
    "new titles and features",
    "The View From India", "Science For All", "Today's Cache",
    "Click here to read", "Subscribe to our newsletter",
    "Follow us on", "Terms of Use", "Privacy Policy",
    "Advertisement", "Sponsored", "Read more", "Also Read",
    "Related News", "All rights reserved", "Copyright",
    "2026e-Paper", "First Day First Show", "Data Point",
    "Health Matters", "The Hindu On Books", "e-Paper",
    "BACK TO TOP",
    "Terms & conditions",
    "Institutional Subscriber",
    "Comments have to be in English",
    "abide by our community guidelines",
    "migrated to a new commenting platform",
    "registered user of The Hindu",
    "access their older comments by logging",
    "Vuukle"
]

def clean_text_strictly(text):
    if not text: return ""
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        

        is_bad = False
        for phrase in KILL_PHRASES:
            if phrase.lower() in line.lower():
                is_bad = True
                break
        
        
        if re.search(r'(published|updated).*-\s*[a-z]+\s+\d{1,2}', line.lower()):
            is_bad = True

        if not is_bad:
            cleaned_lines.append(line)
            
    return "\n".join(cleaned_lines)

def process_cleaning():
    print("Step 2: Cleaning & Archiving...")
    
    
    if not os.path.exists("1.json"):
        print("No raw data found.")
        return

    with open("1.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    clean_data_list = []
    
    
    for item in raw_data:
        original_text = item['content']
        cleaned_text = clean_text_strictly(original_text)
        
        
        if len(cleaned_text) > 100:
            item['content'] = cleaned_text
            clean_data_list.append(item)
    
    
    with open("1.json", "w", encoding="utf-8") as f:
        json.dump(clean_data_list, f, indent=4, ensure_ascii=False)
    print(f"✅ 1.json cleaned. Articles: {len(clean_data_list)}")

    
    all_archive_data = []
    if os.path.exists("2.json"):
        try:
            with open("2.json", "r", encoding="utf-8") as f:
                all_archive_data = json.load(f)
        except: pass
    
    new_entries = []
    for news in clean_data_list:
        if not any(old['link'] == news['link'] for old in all_archive_data):
            new_entries.append(news)
    
    if new_entries:
        
        final_archive = new_entries + all_archive_data
    
        with open("2.json", "w", encoding="utf-8") as f:
            json.dump(final_archive[:100], f, indent=4, ensure_ascii=False)
        print(f"✅ 2.json updated with {len(new_entries)} new articles.")
    else:
        print("ℹ️ No new unique articles for archive.")

if __name__ == "__main__":
    process_cleaning()
