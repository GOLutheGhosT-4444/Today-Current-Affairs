import json
import os
import datetime
import re

def clean_and_store():
    print("🧹 Step 4: Running Smart AI-Output Cleaner...")

    # --- 1. Load Data from 3.json ---
    if not os.path.exists("3.json"):
        print("❌ Error: '3.json' nahi mila.")
        return

    with open("3.json", "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("❌ Error: '3.json' corrupted hai.")
            return

    cleaned_data = []
    removed_count = 0

    # Exact API Errors ki list (No generic words)
    API_ERRORS = [
        "api error", "quota exceeded", "429", "too many requests", 
        "invalid api key", "internal server error", "overloaded"
    ]

    # --- 2. Remove Bad Entries & Clean Content ---
    for item in data:
        content = item.get('content', '').strip()
        title = item.get('title', 'No Title')

        # Check 1: Smart API Errors Check
        is_corrupted = False
        content_lower = content.lower()
        
        for err in API_ERRORS:
            if err in content_lower and len(content) < 150: # API errors aam taur par chote hote hain
                is_corrupted = True
                break
        
        if is_corrupted or content == "REJECT": # Agar humne AI ko REJECT bolne sikhaya tha
            print(f"⚠️ Removing API Error/Rejected: {title[:40]}...")
            removed_count += 1
            continue 

        # Check 2: Smart AI Chatter Remover (Regex)
        # Ye kisi bhi sentence ko hatayega jo "Here", "Sure", "Summary" se shuru ho aur colon (:) pe khatam ho.
        content = re.sub(r'^(Here|Sure|Okay|Summary|Below).*?:\s*\n*', '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Ek aur regex: Agar AI ne koi ek general line likhi hai bullet points se pehle, usko uda do
        content = re.sub(r'^[^•\*\-0-9].*?:[\r\n]+', '', content, count=1)

        # Updated content wapas item me save karein (extra spaces trim karke)
        item['content'] = content.strip()
        cleaned_data.append(item)

    # --- 3. Save Back to 3.json (For Today's PWA Frontend) ---
    with open("3.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    print(f"✅ '3.json' Cleaned! Removed {removed_count} failed items.")

    # --- 4. Smart Backup (Using JSON instead of TXT) ---
    # Hum ek 'archive.json' banayenge. Isse tumhara backend kabhi bhi old data fetch kar sakta hai.
    archive_file = "archive_news.json"
    archive_data = []

    if os.path.exists(archive_file):
        with open(archive_file, "r", encoding="utf-8") as f:
            try:
                archive_data = json.load(f)
            except json.JSONDecodeError:
                archive_data = []

    # Duplicates se bachne ke liye existing links extract karo
    existing_links = {item['link'] for item in archive_data}

    new_additions = 0
    for item in cleaned_data:
        if item['link'] not in existing_links:
            # Add timestamp for the archive
            item['archived_on'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            archive_data.append(item)
            new_additions += 1

    if new_additions > 0:
        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(archive_data, f, indent=4, ensure_ascii=False)
        print(f"✅ {new_additions} fresh articles securely backed up in 'archive_news.json'.")
    else:
        print("ℹ️ No new articles to backup today.")

if __name__ == "__main__":
    clean_and_store()