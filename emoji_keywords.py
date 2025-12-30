# Archivo centralizado de emojis para Petra
# Este es el ÚNICO lugar donde se definen los emojis y sus keywords
# Para agregar más emojis, añádelos a ALL_EMOJIS y opcionalmente a EMOJI_KEYWORDS

# Lista maestra de todos los emojis disponibles
ALL_EMOJIS = [
    # Caras felices
    "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃",
    "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "☺️", "😚",
    "😙", "🥲", "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭",
    "🤫", "🤔", "🤐", "🤨", "😐", "😑", "😶", "😏", "😒", "🙄",
    "😬", "🤥", "😌", "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕",
    "🤢", "🤮", "🤧", "🥵", "🥶", "🥴", "😵", "🤯", "🤠", "🥳",
    "🥸", "😎", "🤓", "🧐", "😕", "😟", "🙁", "☹️", "😮", "😯",
    "😲", "😳", "🥺", "😦", "😧", "😨", "😰", "😥", "😢", "😭",
    "😱", "😖", "😣", "😞", "😓", "😩", "😫", "🥱", "😤", "😡",
    "😠", "🤬", "😈", "👿", "💀", "☠️", "💩", "🤡", "👹", "👺",
    # Manos y gestos
    "👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤌", "🤏", "✌️", "🤞",
    "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👍",
    "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝",
    "🙏", "✍️", "💅", "🤳", "💪", "🦾", "🦿", "🦵", "🦶", "👂",
    "🦻", "👃", "🧠", "🫀", "🫁", "🦷", "🦴", "👀", "👁️", "👅",
    "👄", "👶", "🧒", "👦", "👧", "🧑", "👱", "👨", "🧔", "👨‍🦰",
    # Corazones
    "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
    "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "☮️",
    # Símbolos religiosos y zodíaco
    "✝️", "☪️", "🕉️", "☸️", "✡️", "🔯", "🕎", "☯️", "☦️", "🛐",
    "⛎", "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐",
    "♑", "♒", "♓", "🆔", "⚛️", "🉑", "☢️", "☣️", "📴", "📳",
    # Relojes y tiempo
    "🕛", "🕧", "🕐", "🕜", "🕑", "🕝", "🕒", "🕞", "🕓", "🕟",
    "🕔", "🕠", "🕕", "🕡", "🕖", "🕢", "🕗", "🕣", "🕘", "🕤",
    "🕙", "🕥", "🕚", "🕦", "⌛", "⏳", "⌚", "⏰", "⏱️", "⏲️",
    "🕰️", "🌡️", "⛈️", "🌩️", "🌧️", "☀️", "🌤️", "⛅", "🌥️", "☁️",
    # Flechas y símbolos
    "↩️", "↪️", "⚡", "♻️", "📛", "🔰", "🔱", "⭕", "✅", "☑️",
    "✔️", "❌", "❎", "➰", "➿", "〽️", "✳️", "❇️", "▪️", "▫️",
    "◾", "◽", "◼️", "◻️", "⬛", "⬜", "🔶", "🔷", "🔸", "🔹",
    # Símbolos adicionales
    "⭐", "🌟", "💫", "💥", "💢", "💯", "🔥", "🌈", "🚫",
    "‼️", "⁉️", "❓", "❔", "❕", "❗", "➕", "➖", "➗", "✖️",
]

# Diccionario de emojis con palabras clave para búsqueda
# Los emojis sin keywords aquí aún aparecerán en la lista, solo no serán buscables por keyword
EMOJI_KEYWORDS = {
    # Caras felices
    "😀": ["grinning", "face", "happy", "smile"],
    "😃": ["grinning", "big eyes", "happy", "smile", "joy"],
    "😄": ["grinning", "smiling eyes", "happy", "laugh"],
    "😁": ["beaming", "grin", "happy", "smile"],
    "😆": ["laughing", "satisfied", "happy", "lol", "xd"],
    "😅": ["sweat", "grinning", "nervous", "awkward"],
    "🤣": ["rofl", "rolling", "laughing", "lol", "lmao"],
    "😂": ["joy", "tears", "laughing", "lol", "crying laughing"],
    "🙂": ["slightly smiling", "smile", "ok", "fine"],
    "🙃": ["upside down", "sarcasm", "silly", "ironic"],
    
    # Caras afectuosas
    "😉": ["wink", "flirt", "playful"],
    "😊": ["blush", "smiling", "happy", "shy", "cute"],
    "😇": ["angel", "innocent", "halo", "blessed"],
    "🥰": ["love", "hearts", "adore", "affection"],
    "😍": ["heart eyes", "love", "crush", "adore"],
    "🤩": ["star struck", "excited", "amazed", "wow", "stars"],
    "😘": ["kiss", "blowing kiss", "love", "flirt"],
    "😗": ["kissing", "kiss", "smooch"],
    "☺️": ["smiling", "relaxed", "happy", "content"],
    "😚": ["kissing", "closed eyes", "kiss", "love"],
    "😙": ["kissing", "smiling eyes", "kiss"],
    "🥲": ["happy cry", "grateful", "touched", "emotional"],
    
    # Caras con lengua
    "😋": ["yummy", "delicious", "food", "tasty", "savoring"],
    "😛": ["tongue", "playful", "silly", "bleh"],
    "😜": ["wink", "tongue", "crazy", "playful", "joking"],
    "🤪": ["zany", "crazy", "wild", "goofy", "silly"],
    "😝": ["squinting", "tongue", "playful", "silly"],
    "🤑": ["money", "rich", "dollar", "greedy", "cash"],
    
    # Caras con manos
    "🤗": ["hug", "hugging", "embrace", "warm"],
    "🤭": ["giggle", "covering mouth", "oops", "shy"],
    "🤫": ["shush", "quiet", "secret", "silence"],
    "🤔": ["thinking", "hmm", "consider", "wondering"],
    
    # Caras neutrales
    "🤐": ["zipper mouth", "secret", "quiet", "mute"],
    "🤨": ["raised eyebrow", "suspicious", "skeptical"],
    "😐": ["neutral", "expressionless", "meh", "blank"],
    "😑": ["expressionless", "annoyed", "unamused"],
    "😶": ["no mouth", "silent", "speechless", "mute"],
    "😏": ["smirk", "smug", "flirt", "sly"],
    "😒": ["unamused", "annoyed", "side eye", "meh"],
    "🙄": ["eye roll", "annoyed", "whatever", "bored"],
    
    # Caras durmientes/cansadas
    "😬": ["grimacing", "awkward", "nervous", "cringe"],
    "🤥": ["lying", "pinocchio", "lie", "liar"],
    "😌": ["relieved", "peaceful", "content", "calm"],
    "😔": ["pensive", "sad", "disappointed", "down"],
    "😪": ["sleepy", "tired", "drowsy"],
    "🤤": ["drooling", "hungry", "want", "desire"],
    "😴": ["sleeping", "zzz", "asleep", "tired"],
    
    # Caras enfermas
    "😷": ["mask", "sick", "medical", "covid", "flu"],
    "🤒": ["thermometer", "fever", "sick", "ill"],
    "🤕": ["bandage", "hurt", "injured", "head"],
    "🤢": ["nauseated", "sick", "gross", "disgusted"],
    "🤮": ["vomiting", "sick", "puke", "gross"],
    "🤧": ["sneezing", "sick", "cold", "tissue"],
    "🥵": ["hot", "heat", "sweating", "burning"],
    "🥶": ["cold", "freezing", "frozen", "ice"],
    "🥴": ["woozy", "drunk", "dizzy", "tipsy"],
    "😵": ["dizzy", "dead", "knocked out", "spiral"],
    "🤯": ["mind blown", "exploding", "shocked", "amazed"],
    
    # Caras con accesorios
    "🤠": ["cowboy", "yeehaw", "western", "hat"],
    "🥳": ["party", "celebration", "birthday", "celebrate"],
    "🥸": ["disguised", "glasses", "mustache", "incognito"],
    "😎": ["cool", "sunglasses", "awesome", "chill"],
    "🤓": ["nerd", "geek", "glasses", "smart"],
    "🧐": ["monocle", "thinking", "inspect", "curious"],
    
    # Caras preocupadas
    "😕": ["confused", "puzzled", "unsure"],
    "😟": ["worried", "concerned", "anxious"],
    "🙁": ["frowning", "sad", "disappointed"],
    "☹️": ["frowning", "sad", "unhappy"],
    "😮": ["surprised", "open mouth", "wow", "oh"],
    "😯": ["hushed", "surprised", "stunned"],
    "😲": ["astonished", "shocked", "wow", "surprised"],
    "😳": ["flushed", "embarrassed", "blushing", "shy"],
    "🥺": ["pleading", "puppy eyes", "please", "begging"],
    "😦": ["frowning", "open mouth", "worried"],
    "😧": ["anguished", "worried", "distressed"],
    "😨": ["fearful", "scared", "frightened", "afraid"],
    "😰": ["anxious", "sweat", "nervous", "worried"],
    "😥": ["sad", "relieved", "disappointed"],
    "😢": ["crying", "sad", "tear", "upset"],
    "😭": ["loudly crying", "sobbing", "sad", "tears"],
    "😱": ["screaming", "fear", "scared", "horror", "omg"],
    "😖": ["confounded", "frustrated", "upset"],
    "😣": ["persevering", "struggling", "frustrated"],
    "😞": ["disappointed", "sad", "dejected"],
    "😓": ["downcast", "sweat", "hard work", "tired"],
    "😩": ["weary", "tired", "frustrated", "exhausted"],
    "😫": ["tired", "exhausted", "fed up"],
    "🥱": ["yawning", "tired", "sleepy", "bored"],
    
    # Caras enojadas
    "😤": ["huffing", "angry", "frustrated", "triumph"],
    "😡": ["angry", "mad", "rage", "furious"],
    "😠": ["angry", "mad", "annoyed", "grumpy"],
    "🤬": ["cursing", "swearing", "angry", "mad", "symbols"],
    
    # Caras negativas/fantasía
    "😈": ["devil", "evil", "smiling", "mischief", "naughty"],
    "👿": ["angry devil", "evil", "imp", "mad"],
    "💀": ["skull", "dead", "death", "skeleton"],
    "☠️": ["skull crossbones", "death", "danger", "poison"],
    "💩": ["poop", "poo", "shit", "crap"],
    "🤡": ["clown", "funny", "circus", "joker"],
    "👹": ["ogre", "monster", "japanese", "demon"],
    "👺": ["goblin", "tengu", "japanese", "mask"],
    
    # Manos saludando
    "👋": ["wave", "hello", "hi", "bye", "goodbye"],
    "🤚": ["raised back", "hand", "stop"],
    "🖐️": ["hand", "fingers", "five", "high five"],
    "✋": ["raised hand", "stop", "high five"],
    "🖖": ["vulcan", "spock", "star trek", "live long"],
    
    # Gestos con manos
    "👌": ["ok", "okay", "perfect", "good"],
    "🤌": ["pinched fingers", "italian", "chef kiss"],
    "🤏": ["pinching", "small", "tiny", "little"],
    "✌️": ["peace", "victory", "two", "v sign"],
    "🤞": ["crossed fingers", "luck", "hope", "wish"],
    "🤟": ["love you", "rock", "gesture", "ily"],
    "🤘": ["rock", "metal", "horns", "devil"],
    "🤙": ["call me", "shaka", "hang loose", "phone"],
    
    # Direcciones
    "👈": ["pointing left", "left", "direction"],
    "👉": ["pointing right", "right", "direction"],
    "👆": ["pointing up", "up", "direction"],
    "🖕": ["middle finger", "fuck", "rude", "offensive"],
    "👇": ["pointing down", "down", "direction"],
    "☝️": ["index up", "one", "point", "attention"],
    
    # Pulgares
    "👍": ["thumbs up", "like", "good", "yes", "ok", "approve"],
    "👎": ["thumbs down", "dislike", "bad", "no", "disapprove"],
    
    # Puños
    "✊": ["raised fist", "power", "solidarity", "punch"],
    "👊": ["fist bump", "punch", "bro"],
    "🤛": ["left fist", "fist bump"],
    "🤜": ["right fist", "fist bump"],
    
    # Aplausos y manos juntas
    "👏": ["clap", "applause", "bravo", "congrats"],
    "🙌": ["raising hands", "celebration", "praise", "hooray"],
    "👐": ["open hands", "hug", "jazz hands"],
    "🤲": ["palms up", "prayer", "offering"],
    "🤝": ["handshake", "deal", "agreement", "partnership"],
    "🙏": ["pray", "please", "thank you", "hope", "namaste"],
    
    # Manos haciendo cosas
    "✍️": ["writing", "pen", "signature", "author"],
    "💅": ["nail polish", "nails", "beauty", "sassy"],
    "🤳": ["selfie", "phone", "photo", "camera"],
    
    # Cuerpo
    "💪": ["muscle", "strong", "flex", "bicep", "strength"],
    "🦾": ["mechanical arm", "robot", "prosthetic", "bionic"],
    "🦿": ["mechanical leg", "prosthetic", "bionic"],
    "🦵": ["leg", "kick", "limb"],
    "🦶": ["foot", "kick", "stomp"],
    "👂": ["ear", "listen", "hear", "hearing"],
    "🦻": ["ear aid", "hearing", "deaf"],
    "👃": ["nose", "smell", "sniff"],
    "🧠": ["brain", "smart", "think", "mind", "intelligence"],
    "🫀": ["heart organ", "anatomical", "cardio"],
    "🫁": ["lungs", "breathe", "respiratory"],
    "🦷": ["tooth", "dentist", "teeth"],
    "🦴": ["bone", "skeleton", "dog"],
    "👀": ["eyes", "look", "see", "watching", "stare"],
    "👁️": ["eye", "see", "look", "watch"],
    "👅": ["tongue", "lick", "taste"],
    "👄": ["mouth", "lips", "kiss"],
    
    # Personas
    "👶": ["baby", "infant", "child", "newborn"],
    "🧒": ["child", "kid", "young"],
    "👦": ["boy", "male", "child", "kid"],
    "👧": ["girl", "female", "child", "kid"],
    "🧑": ["person", "adult", "human"],
    "👱": ["blond", "blonde", "person"],
    "👨": ["man", "male", "guy", "adult"],
    "🧔": ["beard", "man", "bearded"],
    "👨‍🦰": ["man", "red hair", "ginger", "redhead"],
    
    # Corazones
    "❤️": ["red heart", "love", "like", "romance"],
    "🧡": ["orange heart", "love", "friendship"],
    "💛": ["yellow heart", "love", "friendship", "happy"],
    "💚": ["green heart", "love", "nature", "envy"],
    "💙": ["blue heart", "love", "trust", "loyalty"],
    "💜": ["purple heart", "love", "compassion"],
    "🖤": ["black heart", "love", "dark", "goth"],
    "🤍": ["white heart", "love", "pure", "clean"],
    "🤎": ["brown heart", "love", "earth"],
    "💔": ["broken heart", "heartbreak", "sad", "breakup"],
    "❣️": ["heart exclamation", "love", "emphasis"],
    "💕": ["two hearts", "love", "romance", "couple"],
    "💞": ["revolving hearts", "love", "romance"],
    "💓": ["beating heart", "love", "alive", "pulse"],
    "💗": ["growing heart", "love", "affection"],
    "💖": ["sparkling heart", "love", "excitement"],
    "💘": ["heart arrow", "cupid", "love", "romance"],
    "💝": ["heart ribbon", "gift", "love", "present"],
    "💟": ["heart decoration", "love", "ornament"],
    
    # Símbolos religiosos
    "☮️": ["peace", "peace symbol", "hippie"],
    "✝️": ["cross", "christian", "religion", "jesus"],
    "☪️": ["star crescent", "islam", "muslim", "religion"],
    "🕉️": ["om", "hindu", "buddhist", "religion"],
    "☸️": ["wheel dharma", "buddhist", "religion"],
    "✡️": ["star david", "jewish", "judaism", "religion"],
    "🔯": ["six pointed star", "jewish"],
    "🕎": ["menorah", "jewish", "hanukkah"],
    "☯️": ["yin yang", "balance", "taoism", "harmony"],
    "☦️": ["orthodox cross", "christian", "religion"],
    "🛐": ["place worship", "pray", "religion"],
    
    # Zodíaco
    "⛎": ["ophiuchus", "zodiac", "astrology"],
    "♈": ["aries", "zodiac", "astrology", "ram"],
    "♉": ["taurus", "zodiac", "astrology", "bull"],
    "♊": ["gemini", "zodiac", "astrology", "twins"],
    "♋": ["cancer", "zodiac", "astrology", "crab"],
    "♌": ["leo", "zodiac", "astrology", "lion"],
    "♍": ["virgo", "zodiac", "astrology"],
    "♎": ["libra", "zodiac", "astrology", "scales"],
    "♏": ["scorpio", "zodiac", "astrology", "scorpion"],
    "♐": ["sagittarius", "zodiac", "astrology", "archer"],
    "♑": ["capricorn", "zodiac", "astrology", "goat"],
    "♒": ["aquarius", "zodiac", "astrology", "water"],
    "♓": ["pisces", "zodiac", "astrology", "fish"],
    
    # Símbolos varios
    "🆔": ["id", "identity", "identification"],
    "⚛️": ["atom", "science", "physics", "nuclear"],
    "🉑": ["accept", "japanese", "ok"],
    "☢️": ["radioactive", "nuclear", "radiation", "danger"],
    "☣️": ["biohazard", "danger", "toxic", "biological"],
    "📴": ["mobile off", "phone off", "silent"],
    "📳": ["vibration", "phone", "mobile"],
    
    # Relojes
    "🕛": ["twelve oclock", "clock", "time", "12"],
    "🕧": ["twelve thirty", "clock", "time", "12:30"],
    "🕐": ["one oclock", "clock", "time", "1"],
    "🕜": ["one thirty", "clock", "time", "1:30"],
    "🕑": ["two oclock", "clock", "time", "2"],
    "🕝": ["two thirty", "clock", "time", "2:30"],
    "🕒": ["three oclock", "clock", "time", "3"],
    "🕞": ["three thirty", "clock", "time", "3:30"],
    "🕓": ["four oclock", "clock", "time", "4"],
    "🕟": ["four thirty", "clock", "time", "4:30"],
    "🕔": ["five oclock", "clock", "time", "5"],
    "🕠": ["five thirty", "clock", "time", "5:30"],
    "🕕": ["six oclock", "clock", "time", "6"],
    "🕡": ["six thirty", "clock", "time", "6:30"],
    "🕖": ["seven oclock", "clock", "time", "7"],
    "🕢": ["seven thirty", "clock", "time", "7:30"],
    "🕗": ["eight oclock", "clock", "time", "8"],
    "🕣": ["eight thirty", "clock", "time", "8:30"],
    "🕘": ["nine oclock", "clock", "time", "9"],
    "🕤": ["nine thirty", "clock", "time", "9:30"],
    "🕙": ["ten oclock", "clock", "time", "10"],
    "🕥": ["ten thirty", "clock", "time", "10:30"],
    "🕚": ["eleven oclock", "clock", "time", "11"],
    "🕦": ["eleven thirty", "clock", "time", "11:30"],
    "⌛": ["hourglass", "time", "waiting", "sand"],
    "⏳": ["hourglass flowing", "time", "waiting", "sand"],
    "⌚": ["watch", "time", "wristwatch"],
    "⏰": ["alarm clock", "time", "wake up", "morning"],
    "⏱️": ["stopwatch", "time", "timer", "sports"],
    "⏲️": ["timer clock", "time", "countdown", "cooking"],
    "🕰️": ["mantelpiece clock", "time", "antique"],
    
    # Clima
    "🌡️": ["thermometer", "temperature", "weather", "fever"],
    "⛈️": ["thunderstorm", "rain", "weather", "lightning"],
    "🌩️": ["lightning", "thunder", "storm", "weather"],
    "🌧️": ["rain", "rainy", "weather", "cloud"],
    "☀️": ["sun", "sunny", "weather", "bright", "hot"],
    "🌤️": ["sun clouds", "partly cloudy", "weather"],
    "⛅": ["sun cloud", "partly cloudy", "weather"],
    "🌥️": ["sun behind cloud", "cloudy", "weather"],
    "☁️": ["cloud", "cloudy", "weather", "overcast"],
    
    # Flechas y símbolos
    "↩️": ["back arrow", "return", "undo"],
    "↪️": ["forward arrow", "redo", "next"],
    "⚡": ["lightning", "bolt", "electricity", "power", "fast", "zap"],
    "♻️": ["recycle", "environment", "green", "eco"],
    "📛": ["name badge", "id", "tag"],
    "🔰": ["beginner", "japanese", "new", "starter"],
    "🔱": ["trident", "poseidon", "neptune", "emblem"],
    "⭕": ["circle", "red circle", "hollow"],
    "✅": ["check", "done", "complete", "yes", "correct"],
    "☑️": ["check box", "done", "complete", "yes"],
    "✔️": ["check mark", "done", "correct", "yes"],
    "❌": ["cross", "no", "wrong", "error", "delete", "x"],
    "❎": ["cross mark", "no", "wrong", "error"],
    "➰": ["curly loop", "loop"],
    "➿": ["double curly loop", "loop"],
    "〽️": ["part alternation", "japanese"],
    "✳️": ["eight spoked asterisk", "star"],
    "❇️": ["sparkle", "star", "shine"],
    "▪️": ["black square", "small", "dot"],
    "▫️": ["white square", "small", "dot"],
    "◾": ["black medium square"],
    "◽": ["white medium square"],
    "◼️": ["black square", "medium"],
    "◻️": ["white square", "medium"],
    "⬛": ["black large square", "dark"],
    "⬜": ["white large square", "light"],
    "🔶": ["orange diamond", "large"],
    "🔷": ["blue diamond", "large"],
    "🔸": ["orange diamond", "small"],
    "🔹": ["blue diamond", "small"],
}

def search_emojis(query, emoji_list):
    """
    Busca emojis que coincidan con la query.
    Retorna una lista de emojis que coinciden.
    """
    if not query:
        return emoji_list
    
    query = query.lower().strip()
    results = []
    
    for emoji in emoji_list:
        # Buscar en keywords
        keywords = EMOJI_KEYWORDS.get(emoji, [])
        if any(query in keyword.lower() for keyword in keywords):
            results.append(emoji)
    
    return results
