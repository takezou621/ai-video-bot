"""
Text Normalizer - Prepares text for TTS by converting English terms to Katakana
Uses a custom dictionary first, then falls back to 'alkana' library for general English words.
Enhanced with number/date/time normalization for natural Japanese speech.
"""
import re
import html
import alkana
from typing import List, Tuple


def decode_html_entities(text: str) -> str:
    """
    Decode HTML entities like &#8217; to their actual characters.
    """
    if not text:
        return text
    # Decode HTML entities (&#8217; -> ', &amp; -> &, etc.)
    text = html.unescape(text)
    return text


def remove_long_english_phrases(text: str, max_english_words: int = 5) -> str:
    """
    Remove or mark long English phrases that shouldn't be read phonetically.
    English phrases longer than max_english_words will be removed.

    This prevents the TTS from awkwardly reading English sentences
    character by character.
    """
    if not text:
        return text

    # Pattern to match sequences of English words (5+ words)
    # This captures things like "For large retailers, the challenge..."
    def replace_long_english(match):
        phrase = match.group(0)
        word_count = len(phrase.split())
        if word_count > max_english_words:
            # P0 Fix: Do NOT remove long English phrases. 
            # Deletion causes loss of proper nouns/names. 
            # Return as-is to be handled by alkana/reading conversion later.
            return phrase
        return phrase

    # Match sequences of English words with punctuation
    # Matches: "word word word, word word."
    pattern = r'(?:[A-Za-z]+[\s,.\-\'\';:]*){' + str(max_english_words + 1) + r',}'
    text = re.sub(pattern, replace_long_english, text)

    # Clean up any resulting double spaces or orphaned punctuation
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([。、！？])', r'\1', text)
    text = re.sub(r'([。、！？])\s*\1+', r'\1', text)

    return text.strip()

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


# ============================================
# Number and Date Normalization for TTS
# ============================================

# Japanese number readings
_NUM_READINGS = {
    '0': 'ゼロ', '1': 'いち', '2': 'に', '3': 'さん', '4': 'よん',
    '5': 'ご', '6': 'ろく', '7': 'なな', '8': 'はち', '9': 'きゅう',
}

_LARGE_UNITS = [
    (10**16, '京'),
    (10**12, '兆'),
    (10**8, '億'),
    (10**4, '万'),
]


def _number_to_japanese(num: int) -> str:
    """Convert integer to natural Japanese reading."""
    if num == 0:
        return 'ゼロ'
    if num < 0:
        return 'マイナス' + _number_to_japanese(-num)

    result = []

    for unit_val, unit_name in _LARGE_UNITS:
        if num >= unit_val:
            count = num // unit_val
            num %= unit_val
            if count == 1:
                result.append(unit_name)
            else:
                result.append(_small_number_to_japanese(count) + unit_name)

    if num > 0:
        result.append(_small_number_to_japanese(num))

    return ''.join(result)


def _small_number_to_japanese(num: int) -> str:
    """Convert number < 10000 to Japanese."""
    if num == 0:
        return ''

    result = []

    # 千 (sen)
    if num >= 1000:
        count = num // 1000
        num %= 1000
        if count == 1:
            result.append('せん')
        elif count == 3:
            result.append('さんぜん')  # Special reading
        elif count == 8:
            result.append('はっせん')  # Special reading
        else:
            result.append(_NUM_READINGS[str(count)] + 'せん')

    # 百 (hyaku)
    if num >= 100:
        count = num // 100
        num %= 100
        if count == 1:
            result.append('ひゃく')
        elif count == 3:
            result.append('さんびゃく')  # Special reading
        elif count == 6:
            result.append('ろっぴゃく')  # Special reading
        elif count == 8:
            result.append('はっぴゃく')  # Special reading
        else:
            result.append(_NUM_READINGS[str(count)] + 'ひゃく')

    # 十 (juu)
    if num >= 10:
        count = num // 10
        num %= 10
        if count == 1:
            result.append('じゅう')
        else:
            result.append(_NUM_READINGS[str(count)] + 'じゅう')

    # 1-9
    if num > 0:
        result.append(_NUM_READINGS[str(num)])

    return ''.join(result)


def _normalize_dates(text: str) -> str:
    """Normalize date formats to natural Japanese."""
    # YYYY/MM/DD or YYYY-MM-DD
    def replace_date(m):
        year, month, day = m.groups()
        return f'{year}年{int(month)}月{int(day)}日'

    text = re.sub(r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', replace_date, text)

    # MM/DD
    def replace_short_date(m):
        month, day = m.groups()
        return f'{int(month)}月{int(day)}日'

    text = re.sub(r'(?<!\d)(\d{1,2})[/](\d{1,2})(?!\d)', replace_short_date, text)

    return text


def _normalize_times(text: str) -> str:
    """Normalize time formats."""
    # HH:MM:SS
    def replace_time_hms(m):
        h, m_val, s = m.groups()
        return f'{int(h)}時{int(m_val)}分{int(s)}秒'

    text = re.sub(r'(\d{1,2}):(\d{2}):(\d{2})', replace_time_hms, text)

    # HH:MM (but not inside timestamp markers like (0:00))
    def replace_time_hm(m):
        h, m_val = m.groups()
        return f'{int(h)}時{int(m_val)}分'

    # Only replace times not in parentheses (timestamp markers)
    text = re.sub(r'(?<![(\d])(\d{1,2}):(\d{2})(?![)\d:])', replace_time_hm, text)

    return text


def _normalize_percentages(text: str) -> str:
    """Normalize percentage formats."""
    def replace_pct(m):
        num = m.group(1)
        if '.' in num:
            int_part, dec_part = num.split('.')
            return f'{int_part}点{dec_part}パーセント'
        return f'{num}パーセント'

    text = re.sub(r'(\d+\.?\d*)%', replace_pct, text)
    return text


def _normalize_currency(text: str) -> str:
    """Normalize currency formats."""
    # $X.XX
    def replace_dollar(m):
        num = m.group(1)
        if '.' in num:
            int_part, dec_part = num.split('.')
            return f'{int_part}ドル{dec_part}セント'
        return f'{num}ドル'

    text = re.sub(r'\$(\d+\.?\d*)', replace_dollar, text)

    # ¥X,XXX or XXX円
    def replace_yen(m):
        num = m.group(1).replace(',', '')
        return f'{_number_to_japanese(int(num))}円'

    text = re.sub(r'[¥￥](\d[\d,]*)', replace_yen, text)

    return text


def _normalize_large_numbers(text: str) -> str:
    """Normalize large numbers with units."""
    # X億, X兆, X万 - already in Japanese format
    # Just convert the number part
    def replace_with_unit(m):
        num = m.group(1).replace(',', '')
        unit = m.group(2)
        try:
            return _number_to_japanese(int(float(num))) + unit
        except:
            return m.group(0)

    text = re.sub(r'(\d[\d,.]*)(億|兆|万|円|ドル|ウォン)', replace_with_unit, text)

    return text


def _normalize_model_versions(text: str) -> str:
    """Normalize model version numbers like GPT-5.2, Gemini 3."""
    # X.Y versions
    def replace_version(m):
        major, minor = m.groups()
        return f'{major}点{minor}'

    text = re.sub(r'(\d+)\.(\d+)(?=\s|$|[^\d])', replace_version, text)

    return text


def normalize_for_tts_advanced(text: str) -> str:
    """
    Advanced normalization for TTS including numbers, dates, currency.
    Call this BEFORE normalize_text_for_tts() for best results.
    """
    if not text:
        return text

    # Step 0: Decode HTML entities first (&#8217; -> ', &amp; -> &, etc.)
    text = decode_html_entities(text)

    # Step 0.5: Remove long English phrases that would sound terrible when read phonetically
    text = remove_long_english_phrases(text, max_english_words=5)

    # Order matters: more specific patterns first
    text = _normalize_dates(text)
    text = _normalize_times(text)
    text = _normalize_currency(text)
    text = _normalize_percentages(text)
    text = _normalize_large_numbers(text)
    text = _normalize_model_versions(text)

    return text


# ============================================
# Text Chunking for TTS
# ============================================

def split_into_chunks(text: str, max_chars: int = 80, min_chars: int = 20) -> List[str]:
    """
    Split text into chunks suitable for TTS processing.

    Args:
        text: Text to split
        max_chars: Maximum characters per chunk (default: 80)
        min_chars: Minimum characters to avoid too-short chunks (default: 20)

    Returns:
        List of text chunks
    """
    if not text or len(text) <= max_chars:
        return [text] if text else []

    chunks = []
    remaining = text.strip()

    # Priority split points (in order)
    split_patterns = [
        r'。',           # Full stop
        r'！',          # Exclamation
        r'？',          # Question
        r'、',           # Comma
        r'）',          # Close paren
        r'」',          # Close quote
        r'\n',           # Newline
        r'　',          # Full-width space
        r' ',            # Space
    ]

    while len(remaining) > max_chars:
        # Look for split point within max_chars
        best_split = -1

        for pattern in split_patterns:
            # Search from the end of the allowed range backwards
            for i in range(min(max_chars, len(remaining)), min_chars - 1, -1):
                if re.match(pattern, remaining[i-1:i]):
                    best_split = i
                    break
            if best_split > 0:
                break

        if best_split <= 0:
            # No good split point found, force split at max_chars
            best_split = max_chars

        chunk = remaining[:best_split].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[best_split:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


def normalize_and_chunk(text: str, max_chars: int = 80) -> List[str]:
    """
    Complete normalization and chunking pipeline for TTS.

    Args:
        text: Raw text to process
        max_chars: Maximum characters per chunk

    Returns:
        List of normalized, chunked text segments
    """
    # Step 1: Advanced normalization (numbers, dates, etc.)
    text = normalize_for_tts_advanced(text)

    # Step 2: English to Katakana conversion
    text = normalize_text_for_tts(text)

    # Step 3: Split into chunks
    chunks = split_into_chunks(text, max_chars=max_chars)

    return chunks

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
