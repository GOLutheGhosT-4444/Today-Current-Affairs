import re
import string

class UniversalNewsCleaner:
    def __init__(self):
        # 1. UNIVERSAL JUNK LIST (Ye har news site par milega)
        self.junk_patterns = [
            # Social Media & Sharing
            r"follow us on", r"share this article", r"join our whatsapp", 
            r"click here to", r"subscribe to", r"sign up for", 
            r"like us on", r"twitter", r"facebook", r"instagram",
            
            # Promos & Ads
            r"advertisement", r"sponsored", r"read more", r"also read", 
            r"related news", r"watch video", r"photo gallery",
            
            # Legal & Footer
            r"all rights reserved", r"copyright", r"terms of use", 
            r"privacy policy", r"disclaimer", r"contact us",
            
            # Common Newsletter stuff
            r"morning briefing", r"evening digest", r"todays top stories",
            r"loading\.\.\.", r"please wait"
        ]

        # Common English Stopwords (Inhe ignore karenge taaki matching accurate ho)
        self.stopwords = {
            'is', 'am', 'are', 'was', 'were', 'the', 'a', 'an', 'and', 'but', 'or', 
            'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'this', 'that',
            'it', 'he', 'she', 'they', 'we', 'you', 'his', 'her', 'their', 'has', 'have'
        }

    def _clean_text_basic(self, text):
        """Extra spaces aur formatting marks hatata hai"""
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces -> 1 space
        return text.strip()

    def _is_junk_line(self, line):
        """
        Check karta hai ki line faltu hai ya nahi.
        Logic: Chhoti lines, ya jisme junk words ho, wo bekar hain.
        """
        line_lower = line.lower()
        
        # Rule 1: Length Check
        # Agar line 30 characters se chhoti hai aur usme Full Stop (.) nahi hai, 
        # to wo pakka Menu item, Author Name ya Date hai.
        if len(line) < 30 and "." not in line:
            return True

        # Rule 2: Junk Patterns Check (Regex)
        for pattern in self.junk_patterns:
            if re.search(pattern, line_lower):
                return True
                
        return False

    def _get_significant_words(self, text):
        """Text se important Nouns/Verbs nikalta hai (Stopwords hata kar)"""
        # Punctuation hatana
        text = text.lower().translate(str.maketrans('', '', string.punctuation))
        words = set(text.split())
        # Stopwords hatana
        return words - self.stopwords

    def clean_and_validate(self, headline, raw_text):
        """
        Main Function:
        1. Line-by-line safai karta hai.
        2. Relevance check karta hai (Headline vs Body).
        Returns: Clean Text string OR None (agar article bekar hai).
        """
        if not raw_text or not headline:
            return None

        lines = raw_text.split('\n')
        cleaned_lines = []

        # --- STEP 1: Line Filtering ---
        for line in lines:
            line = self._clean_text_basic(line)
            
            if not line: # Empty line skip
                continue
                
            if not self._is_junk_line(line):
                cleaned_lines.append(line)

        # Agar safai ke baad kuch bacha hi nahi
        if len(cleaned_lines) == 0:
            return None

        final_body = " ".join(cleaned_lines)

        # --- STEP 2: Relevance Check (The Logic) ---
        # Agar Scraper ne galti se Sidebar ya Footer utha liya hai, 
        # to Headline ke words Body me match nahi karenge.
        
        headline_words = self._get_significant_words(headline)
        body_words = self._get_significant_words(final_body)

        # Count common words
        common_count = len(headline_words.intersection(body_words))
        
        # Threshold: Kam se kam 2 important words match hone chahiye.
        # (e.g. Headline: "Modi visits France" -> Body me "Modi" aur "France" hone chahiye)
        if common_count < 2:
            # Fallback: Agar article bohot chhota hai (e.g. Breaking news), to 1 word match bhi chalega
            if len(final_body) < 200 and common_count >= 1:
                return final_body
            
            print(f"⚠️  REJECTED: Irrelevant content found for '{headline[:20]}...'")
            return None

        return final_body

# --- USE KAISE KAREIN ---

cleaner = UniversalNewsCleaner()

# Example: Ganda Text (Jisme menu, ads, links bhare hain)
dirty_headline = "SpaceX launches new Starship rocket"
dirty_text = """
Home > Science > Space
Click here to subscribe.
SpaceX successfully launched its massive Starship rocket on Thursday.
Follow us on Twitter for updates.
The rocket lifted off from Texas and reached orbit successfully.
Also Read: NASA's moon mission.
Advertisement.
Copyright 2024.
"""

cleaned_text = cleaner.clean_and_validate(dirty_headline, dirty_text)

print("--- ORIGINAL ---")
print(dirty_text)
print("\n--- CLEANED ---")
print(cleaned_text)
