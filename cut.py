import json
import os
import re

KILL_PHRASES = [
    "Looking at World Affairs", "News and reviews from the world of cinema",
    "Your download of the top 5 technology stories", "The weekly newsletter",
    "takes the jargon out of science", "Decoding the headlines with facts",
    "getting to good health, and staying there", "Books of the week, reviews",
    "The View From India", "Science For All", "Today's Cache",
    "Click here to read", "Subscribe to our newsletter", "Follow us on", 
    "Terms of Use", "Privacy Policy", "Advertisement", "Sponsored", 
    "Read more", "Also Read", "Related News", "All rights reserved", 
    "Copyright", "2026e-Paper", "First Day First Show", "Data Point",
    "Health Matters", "The Hindu On Books", "e-Paper", "BACK TO TOP", 
    "Terms & conditions", "Institutional Subscriber", "migrated to a new commenting", 
    "registered user of The Hindu", "access their older comments by logging", 
    "Vuukle", "Representational file image", "Please enter a valid email",
    "Sign in", "Register", "Premium article", "Download our App"
]

def smart_clean_text(text):
    if not text: return ""

    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line: continue

        line_lower = line.lower()
        is_bad = False

        # 1. Direct Kill Phrase Match
        for phrase in KILL_PHRASES:
            if phrase.lower() in line_lower:
                is_bad = True
                break
        if is_bad: continue

        # 2. Strict Date/Author/Source Regex (e.g., "Published: 12 Jan", "By John Doe")
        if re.match(r'^(published|updated|by|source|image)\s*[:\-]?\s*[a-z]+', line_lower):
            continue

        # 3. City & Agency cleanup at the start of a sentence (e.g., "New Delhi: ", "PTI - ")
        # Ye line ko delete nahi karega, bas shuruat ka kachra saaf karega
        line = re.sub(r'^([A-Z][a-zA-Z\s]+(:\s*|—\s*|-\s*))', '', line)

        # 4. Word Count Heuristics (Menu/Tag Remover)
        # Agar line me 4 se kam words hain aur full stop nahi hai, toh wo shayad menu button ya tag hai.
        words = line.split()
        if len(words) <= 4 and not line.endswith('.'):
            continue

        # 5. Social Media & Promo Catcher
        if "@" in line and ("gmail" in line_lower or "yahoo" in line_lower or "contact" in line_lower):
            continue
        if re.search(r'(twitter|facebook|instagram|telegram)\.com', line_lower):
            continue

        cleaned_lines.append(line)

    # 6. Final Formatting: Remove extra blank lines
    final_text = "\n".join(cleaned_lines)
    final_text = re.sub(r'\n{2,}', '\n\n', final_text)
    
    return final_text.strip()

def process_cleaning():
    print("🧹 Step 2: Running Smart Data Cleaner...\n")

    if not os.path.exists("1.json"):
        print("❌ Error: '1.json' nahi mila. Pehle scraper run karo.")
        return

    with open("1.json", "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            print("❌ Error: '1.json' khali ya corrupted hai.")
            return

    clean_data_list = []

    for item in raw_data:
        original_text = item.get('content', '')
        cleaned_text = smart_clean_text(original_text)

        # AI ke liye kam se kam 150 characters hone zaroori hain taaki achhi summary ban sake
        if len(cleaned_text) > 150:
            item['content'] = cleaned_text
            clean_data_list.append(item)

    # Sirf 2.json me clean data save hoga, all.txt completely removed.
    with open("2.json", "w", encoding="utf-8") as f:
        json.dump(clean_data_list, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Success! '2.json' is ready with {len(clean_data_list)} highly purified articles.")

if __name__ == "__main__":
    process_cleaning()
