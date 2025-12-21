"""
Text Normalizer - Prepares text for TTS by converting English terms to Katakana
Uses a custom dictionary first, then falls back to 'alkana' library for general English words.
"""
import re
import alkana

# 1. Custom Dictionary for Tech/AI terms (High Priority)
# These nuances might not be captured correctly by general converters
CUSTOM_DICT = {
    # Corrections
    "コピロット": "コパイロット",
    "コピュラート": "コパイロット",
    "オープンAI": "オープンエーアイ",
    
    # Tech Acronyms (often read alphabet-wise or specific ways)
    "AI": "エーアイ",
    "AGI": "エージーアイ",
    "ASI": "エーエスアイ",
    "LLM": "エルエルエム",
    "LSP": "エルエスピー",
    "API": "エーピーアイ",
    "GUI": "ジーユーアイ",
    "CLI": "シーエルアイ",
    "UI": "ユーアイ",
    "UX": "ユーエックス",
    "CEO": "シーイーオー",
    "CTO": "シーティーオー",
    "CFO": "シーエフオー",
    "AWS": "エーダブリューエス",
    "GCP": "ジーシーピー",
    "PC": "ピーシー",
    "OS": "オーエス",
    "SNS": "エスエヌエス",
    "IOT": "アイオーティー",
    "VR": "ブイアール",
    "AR": "エーアール",
    "MR": "エムアール",
    "XR": "クロスアリアリティ",
    "NFT": "エヌエフティー",
    "SSD": "エスエスディー",
    "HDD": "エイチディーディー",
    "GPU": "ジーピーユー",
    "CPU": "シーピーユー",
    "RAM": "ラム",
    "ROM": "ロム",
    "USB": "ユーエスビー",
    "HDMI": "エイチディーエムアイ",
    "URL": "ユーアールエル",
    "HTTP": "エイチティーティーピー",
    "HTTPS": "エイチティーティーピーエス",
    "HTML": "エイチティーエムエル",
    "SQL": "エスキューエル",
    "JSON": "ジェイソン",
    "PDF": "ピーディーエフ",
    "JPG": "ジェイペグ",
    "PNG": "ピング",
    "GIF": "ジフ",
    "MP4": "エムピーフォー",
    "MP3": "エムピースリー",
    "VS CODE": "ブイエスコード",
    "VSCODE": "ブイエスコード",
    "DALL-E": "ダリ",
    "DALL-E 3": "ダリスリー",
    "GPT-4": "ジーピーティーフォー",
    "GPT-4O": "ジーピーティーフォーオー",
    "GPT": "ジーピーティー",
    "CHATGPT": "チャットジーピーティー",
    "GITHUB": "ギットハブ",
    "OPENAI": "オープンエーアイ",
    "NVIDIA": "エヌビディア",
    "YOUTUBE": "ユーチューブ",
    "GOOGLE": "グーグル",
    "APPLE": "アップル",
    "MICROSOFT": "マイクロソフト",
    "AMAZON": "アマゾン",
    "META": "メタ",
    "FACEBOOK": "フェイスブック",
    "TWITTER": "ツイッター",
    "X": "エックス",
    "INSTAGRAM": "インスタグラム",
    "TIKTOK": "ティックトック",
    "NETFLIX": "ネットフリックス",
    "DISNEY": "ディズニー",
    "SPOTIFY": "スポティファイ",
    "HUGGING FACE": "ハギングフェイス",
    "HUGGINGFACE": "ハギングフェイス",
    "STABILITY AI": "スタビリティエーアイ",
    "MIDJOURNEY": "ミッドジャーニー",
    "ANTHROPIC": "アンソロピック",
    "PERPLEXITY": "パープレキシティ",
    "MISTRAL": "ミストラル",
    "COGNIZANT": "コグニザント",
    "INFOSYS": "インフォシス",
    "WIPRO": "ウィプロ",
    "TATA": "タタ",
    "CONSULTANCY": "コンサルタンシー",
    "SERVICES": "サービシズ",
    "CLAUDE": "クロード",
    "GEMINI": "ジェミニ",
    "COPILOT": "コパイロット",
    "LLAMA": "ラマ",
}

def normalize_text_for_tts(text: str) -> str:
    """
    Normalize text for Japanese TTS.
    1. Apply custom dictionary for Tech terms.
    2. Use 'alkana' library to convert remaining English words to Katakana.
    3. Fallback to simple Katakana conversion for acronyms.
    """
    if not text:
        return text

    normalized = text

    # 1. Custom Dictionary Replacement (Case-insensitive)
    # Sort keys by length to match longest first (e.g. "GPT-4" before "GPT")
    sorted_keys = sorted(CUSTOM_DICT.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        val = CUSTOM_DICT[key]
        # Use regex lookbehind/lookahead to match whole words only
        # (?<![a-zA-Z]) ensures no letter precedes the match
        # (?![a-zA-Z]) ensures no letter follows the match
        pattern = re.compile(r'(?<![a-zA-Z])' + re.escape(key) + r'(?![a-zA-Z])', re.IGNORECASE)
        normalized = pattern.sub(val, normalized)

    # 2. General English Word Conversion using alkana
    # Find all English words (consecutive alphabet characters)
    def replace_english_word(match):
        word = match.group(0)
        
        # Skip if it looks like a variable placeholder or special token
        if word.startswith("{") or word.startswith("<"):
            return word
            
        # Try alkana
        kana = alkana.get_kana(word.lower())
        if kana:
            return kana
            
        # If no kana found, and it's short and uppercase, read as alphabet
        if word.isupper() and len(word) <= 4:
            return _read_alphabet(word)
            
        # If still nothing, leave it (or force simple approximation if critical)
        # Leaving it usually results in "reading letters" by VoiceVox which is annoying but intelligible.
        # But user wants "correct pronunciation".
        return word

    normalized = re.sub(r'[a-zA-Z]+', replace_english_word, normalized)

    return normalized

def _read_alphabet(word: str) -> str:
    """Convert acronyms like 'ABC' to 'エービーシー'"""
    readings = {
        'a': 'エー', 'b': 'ビー', 'c': 'シー', 'd': 'ディー', 'e': 'イー', 'f': 'エフ', 'g': 'ジー',
        'h': 'エイチ', 'i': 'アイ', 'j': 'ジェー', 'k': 'ケー', 'l': 'エル', 'm': 'エム', 'n': 'エヌ',
        'o': 'オー', 'p': 'ピー', 'q': 'キュー', 'r': 'アール', 's': 'エス', 't': 'ティー', 'u': 'ユー',
        'v': 'ブイ', 'w': 'ダブリュー', 'x': 'エックス', 'y': 'ワイ', 'z': 'ゼット'
    }
    return "・".join([readings.get(c.lower(), c) for c in word])

if __name__ == "__main__":
    # Test
    test_sentences = [
        "最新のGitHubとOpenAIのニュース。",
        "MicrosoftのCopilotライセンス。",
        "CognizantやWiproが導入。",
        "Claude Codeの新機能。",
        "Marketing分野でのAI利用。",
        "WPPとStability AIの協力。",
        "My SKILL level is HIGH.",
        "UnknownWordTest"
    ]
    
    for s in test_sentences:
        print(f"In:  {s}")
        print(f"Out: {normalize_text_for_tts(s)}")
        print("-" * 20)
