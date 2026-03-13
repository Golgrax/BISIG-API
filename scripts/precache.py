import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import video_service

# Extensive list of words to precache
WORDS_TO_PRECACHE = [
    # Alphabet
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    # Numbers
    'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty',
    # Greetings & Common Phrases
    "hello", "hi", "goodbye", "bye", "please", "thank you", "thanks", "welcome", "you're welcome",
    "excuse me", "sorry", "yes", "no", "maybe", "help", "stop", "go", "wait", "good", "bad",
    "morning", "afternoon", "night", "evening", "how are you", "what's up", "nice to meet you",
    "name", "sign", "understand", "don't understand", "again", "slow", "fast",
    # Family & People
    "mother", "mom", "father", "dad", "parent", "sister", "brother", "grandmother", "grandma",
    "grandfather", "grandpa", "aunt", "uncle", "cousin", "son", "daughter", "child", "baby",
    "boy", "girl", "man", "woman", "friend", "neighbor", "boss", "coworker", "teacher", "student",
    "doctor", "nurse", "police", "dentist", "family", "husband", "wife", "marriage", "divorce",
    # Pronouns & Questions
    "I", "me", "my", "mine", "you", "your", "yours", "he", "she", "it", "his", "her", "hers",
    "we", "us", "our", "ours", "they", "them", "their", "theirs", "who", "what", "when", "where",
    "why", "how", "which", "how many", "how much",
    # Time & Calendar
    "today", "tomorrow", "yesterday", "now", "later", "soon", "before", "after", "time", "day",
    "week", "month", "year", "hour", "minute", "second", "calendar", "monday", "tuesday",
    "wednesday", "thursday", "friday", "saturday", "sunday", "morning", "noon", "afternoon",
    "night", "midnight", "early", "late", "always", "never", "sometimes", "often", "daily",
    # Colors
    "red", "blue", "yellow", "green", "orange", "purple", "pink", "black", "white", "gray",
    "brown", "gold", "silver", "color", "rainbow",
    # Food & Drink
    "eat", "drink", "hungry", "thirsty", "water", "food", "milk", "juice", "soda", "coffee",
    "tea", "beer", "wine", "apple", "banana", "orange", "grapes", "strawberry", "fruit",
    "vegetable", "bread", "butter", "cheese", "egg", "meat", "chicken", "fish", "beef", "pork",
    "rice", "pasta", "pizza", "hamburger", "sandwich", "soup", "salad", "cookie", "cake", "candy",
    "chocolate", "ice cream", "sugar", "salt", "pepper", "breakfast", "lunch", "dinner", "snack",
    "restaurant", "kitchen", "cook", "bake",
    # Actions (Verbs)
    "run", "walk", "jump", "sit", "stand", "sleep", "wake up", "wash", "brush", "eat", "drink",
    "play", "work", "read", "write", "talk", "speak", "listen", "hear", "see", "look", "watch",
    "think", "know", "learn", "teach", "give", "take", "bring", "buy", "sell", "pay", "cost",
    "make", "build", "break", "fix", "clean", "dirty", "open", "close", "start", "finish",
    "win", "lose", "search", "find", "hide", "laugh", "cry", "smile", "frown", "love", "hate",
    "like", "dislike", "want", "need", "have", "can", "cannot", "must", "should", "will",
    "go", "come", "stay", "leave", "drive", "ride", "fly", "swim", "dance", "sing", "paint",
    "draw", "type", "call", "send", "receive", "help", "practice", "remember", "forget",
    "believe", "hope", "wish", "dream", "wait", "try", "use", "wear", "put", "cut", "push",
    "pull", "carry", "hold", "throw", "catch", "kick", "kick", "hit", "shake", "fall", "climb",
    # Descriptors (Adjectives)
    "big", "small", "tall", "short", "long", "wide", "narrow", "thick", "thin", "heavy", "light",
    "hard", "soft", "hot", "cold", "warm", "cool", "new", "old", "young", "fast", "slow",
    "happy", "sad", "angry", "scared", "excited", "bored", "tired", "busy", "lazy", "smart",
    "dumb", "funny", "serious", "pretty", "beautiful", "ugly", "clean", "dirty", "full", "empty",
    "rich", "poor", "strong", "weak", "easy", "hard", "difficult", "right", "wrong", "true",
    "false", "important", "expensive", "cheap", "loud", "quiet", "dark", "bright", "sweet",
    "sour", "bitter", "salty", "delicious", "disgusting", "wet", "dry", "soft", "rough",
    "smooth", "sharp", "dull", "different", "same", "similar", "another", "only", "best", "worst",
    # Places
    "home", "house", "apartment", "room", "bedroom", "bathroom", "kitchen", "living room",
    "school", "classroom", "office", "work", "store", "market", "mall", "hospital", "bank",
    "library", "park", "beach", "forest", "mountain", "city", "town", "country", "state",
    "world", "earth", "street", "road", "bridge", "church", "temple", "synagogue", "mosque",
    "gym", "theater", "movie", "airport", "station", "bus stop", "hotel", "farm", "zoo",
    # Animals
    "animal", "dog", "cat", "bird", "fish", "horse", "cow", "pig", "sheep", "chicken", "duck",
    "elephant", "lion", "tiger", "bear", "monkey", "rabbit", "mouse", "snake", "frog", "spider",
    "butterfly", "bee", "turtle", "deer", "wolf", "fox", "whale", "dolphin", "shark",
    # Nature & Environment
    "sun", "moon", "star", "sky", "cloud", "rain", "snow", "wind", "storm", "thunder",
    "lightning", "weather", "hot", "cold", "tree", "flower", "grass", "leaf", "plant", "rock",
    "sand", "dirt", "ocean", "sea", "river", "lake", "waterfall", "mountain", "hill", "fire",
    "smoke", "air", "environment", "nature",
    # School & Work
    "school", "college", "university", "class", "homework", "test", "grade", "book", "paper",
    "pen", "pencil", "computer", "internet", "website", "email", "phone", "job", "money",
    "paycheck", "boss", "manager", "meeting", "presentation", "interview", "hire", "fire",
    "retire", "success", "fail", "goal", "plan", "problem", "solution",
    # Health & Body
    "body", "head", "face", "eye", "ear", "nose", "mouth", "tooth", "tongue", "hair", "neck",
    "shoulder", "arm", "elbow", "hand", "finger", "thumb", "chest", "back", "stomach", "leg",
    "knee", "foot", "toe", "heart", "blood", "bone", "skin", "health", "sick", "hurt", "pain",
    "medicine", "pill", "hospital", "doctor", "nurse", "emergency", "fever", "cough", "sneeze",
    "dizzy", "blind", "deaf", "hearing",
    # Clothing & Personal Items
    "clothes", "shirt", "pants", "dress", "skirt", "jacket", "coat", "hat", "shoes", "socks",
    "boots", "gloves", "scarf", "underwear", "pajamas", "watch", "ring", "necklace", "glasses",
    "bag", "backpack", "wallet", "purse", "umbrella", "keys", "phone", "money",
    # Miscellaneous Nouns
    "thing", "idea", "part", "number", "zero", "one", "two", "three", "four", "five", "six",
    "seven", "eight", "nine", "ten", "hundred", "thousand", "million", "billion", "car",
    "truck", "bike", "bicycle", "bus", "train", "plane", "boat", "ship", "box", "bag", "table",
    "chair", "bed", "door", "window", "wall", "floor", "ceiling", "light", "fan", "toy", "game",
    "ball", "gift", "present", "music", "art", "science", "history", "math", "language",
    "english", "spanish", "french", "german", "chinese", "japanese", "sign language", "asl",
    "question", "answer", "truth", "lie", "secret", "peace", "war", "law", "government",
    "president", "country", "flag", "holiday", "birthday", "christmas", "thanksgiving",
    "easter", "halloween", "party", "celebration", "wedding", "funeral", "travel", "vacation",
    "ticket", "passport", "map", "direction", "north", "south", "east", "west", "up", "down",
    "left", "right", "front", "back", "top", "bottom", "middle", "inside", "outside", "near",
    "far", "between", "around", "everywhere", "nowhere"
]

# De-duplicate
WORDS_TO_PRECACHE = sorted(list(set([w.lower().strip() for w in WORDS_TO_PRECACHE])))

async def precache_all():
    print(f"Starting precache for {len(WORDS_TO_PRECACHE)} words/letters...")
    
    for word in WORDS_TO_PRECACHE:
        if not word: continue
        print(f"--- Processing: {word} ---")
        
        try:
            # 1. Fetch Video
            video_info = await video_service.get_or_fetch_video(word)
            if not video_info:
                print(f"  [!] Video not found for: {word}")
                continue
            
            # 2. Extract Skeleton Data (JSON)
            print(f"  [+] Extracting skeleton JSON...")
            skeleton_data = await video_service.get_skeleton_for_video(video_info)
            
            # 3. Generate Skeleton Video (.avi)
            # We skip this for large lists to save space/time, but generate if requested
            # print(f"  [+] Rendering skeleton video...")
            # await video_service.get_skeleton_video_for_word(video_info)
            
            if skeleton_data:
                print(f"  [v] Done: {word}")
            else:
                print(f"  [x] Failed to process skeleton for: {word}")
        except Exception as e:
            print(f"  [Error] {word}: {e}")

if __name__ == "__main__":
    asyncio.run(precache_all())
