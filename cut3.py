import json
import os
import datetime

def clean_and_store():
    print("🧹 Step 4: Cleaning 3.json (Removing API Errors)...")

    # --- 1. Load Data from 3.json ---
    if not os.path.exists("3.json"):
        print("❌ Error: 3.json nahi mila.")
        return

    with open("3.json", "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except:
            print("❌ 3.json corrupted hai.")
            return

    cleaned_data = []
    removed_count = 0

    # --- 2. Remove Bad Entries ---
    for item in data:
        content = item.get('content', '')

        # Check: Kya content me Error code hai?
        # Hum keywords dhoondhenge taaki future me bhi koi error aaye to pakda jaye
        if "API ERROR" in content or "Quota exceeded" in content or "429" in content or "error" in content.lower():
            print(f"⚠️ Removing Corrupted News: {item.get('title', 'No Title')[:30]}...")
            removed_count += 1
            continue # Is item ko skip karo (Delete)

        # Agar sab sahi hai to list me rakho
        cleaned_data.append(item)

    # --- 3. Save Back to 3.json (Overwrite) ---
    # Hum wapas 3.json me hi save kar rahe hain taaki Reader.php ko code change na karna pade
    with open("3.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
    
    print(f"✅ 3.json Cleaned! Removed {removed_count} failed items.")

    # --- 4. Append to all3.txt (Backup) ---
    # Mode 'a' (append) ka use karenge taaki purana data na ude
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open("all3.txt", "a", encoding="utf-8") as f:
        if cleaned_data:
            f.write(f"\n\n--- BATCH ADDED ON {timestamp} ---\n")
            
            for item in cleaned_data:
                f.write(f"{'='*40}\n")
                f.write(f"🛑 {item.get('title', '')}\n")
                f.write(f"{'-'*20}\n")
                f.write(f"{item.get('content', '')}\n")
                f.write(f"\nSource: {item.get('link', '#')}\n")
                f.write(f"{'='*40}\n")
            
            print(f"✅ Valid Data Appended to all3.txt")
        else:
            print("ℹ️ No valid data to append.")

if __name__ == "__main__":
    clean_and_store()
