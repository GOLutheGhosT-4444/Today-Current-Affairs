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
    "Published - February", "Published - January", "Published - March",
    "Updated - February", "Updated - January",
    "Subscribe to our newsletter",
    "The View From India",
    "Science For All",
    "Today's Cache"
]

def clean_text_strictly(text):
    if not text: return ""
    
    splitter = "Looking at World Affairs from the Indian perspective"
    if splitter in text:
        text = text.split(splitter)[0]

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
        
        if re.search(r'(published|updated)\s*-\s*[a-z]+\s+\d{1,2}', line.lower()):
            is_bad = True

        if not is_bad:
            cleaned_lines.append(line)
            
    return "\n".join(cleaned_lines)

def process_cleaning():
    print("Step 2: Cleaning Data...")
    
    if not os.path.exists("1.json"):
        print("No data to clean.")
        return

    with open("1.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    clean_data = []
    for item in data:
        original_text = item['content']
        cleaned_text = clean_text_strictly(original_text)
        
        if len(cleaned_text) > 100:
            item['content'] = cleaned_text
            clean_data.append(item)
    
    with open("1.json", "w", encoding="utf-8") as f:
        json.dump(clean_data, f, indent=4, ensure_ascii=False)
        
    all_data = []
    if os.path.exists("2.json"):
        try:
            with open("2.json", "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except: pass
        
    new_archive = [n for n in clean_data if not any(old['link'] == n['link'] for old in all_data)]
    final_archive = new_archive + all_data
    
    with open("2.json", "w", encoding="utf-8") as f:
        json.dump(final_archive[:100], f, indent=4, ensure_ascii=False)
        
    print(f"Cleaning Done! {len(clean_data)} articles saved.")

if __name__ == "__main__":
    process_cleaning()
