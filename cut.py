import json
import os
import re

KILL_PHRASES = [
    "Looking at World Affairs",
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
    "BACK TO TOP", "Terms & conditions", "Institutional Subscriber",
    "Comments have to be in English", "abide by our community guidelines",
    "migrated to a new commenting platform", "registered user of The Hindu",
    "access their older comments by logging", "Vuukle",
    "Representational file image"
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
    print("Step 2: Cleaning Data...")
    
    
    if not os.path.exists("1.json"):
        print("❌ Error: 1.json nahi mila.")
        return

    with open("1.json", "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            print("❌ Error: 1.json khali ya corrupted hai.")
            return
    
    clean_data_list = []
    
    
    for item in raw_data:
        original_text = item.get('content', '')
        cleaned_text = clean_text_strictly(original_text)
        
    
        if len(cleaned_text) > 100:
            item['content'] = cleaned_text
            clean_data_list.append(item)
    
    
    with open("2.json", "w", encoding="utf-8") as f:
        json.dump(clean_data_list, f, indent=4, ensure_ascii=False)
    print(f"✅ 2.json saved with {len(clean_data_list)} clean articles.")

    
    existing_links = set()
    if os.path.exists("all.txt"):
        with open("all.txt", "r", encoding="utf-8") as f:
            content = f.read()
            
            existing_links = set(re.findall(r'LINK: (http[s]?://\S+)', content))

    new_count = 0
    with open("all.txt", "a", encoding="utf-8") as f:
        for news in clean_data_list:
            if news['link'] not in existing_links:
                f.write(f"\n{'='*50}\n")
                f.write(f"DATE: {news['date']}\n")
                f.write(f"TITLE: {news['title']}\n")
                f.write(f"LINK: {news['link']}\n")
                f.write(f"{'-'*20}\n")
                f.write(f"{news['content']}\n")
                f.write(f"{'='*50}\n")
                new_count += 1
                
    if new_count > 0:
        print(f"✅ all.txt me {new_count} naye articles jod diye gaye.")
    else:
        print("ℹ️ all.txt me koi naya article nahi joda (Duplicate found).")

if __name__ == "__main__":
    process_cleaning()
