"""
English to Katakana Converter
Converts English words to katakana for TTS pronunciation
Uses a combination of dictionary lookup and phonetic rules
"""
import re
from typing import Dict, Optional

# Common English words that appear in tech news → katakana
COMMON_WORDS: Dict[str, str] = {
    # People names
    "moxie": "モキシー",
    "musk": "マスク",
    "elon": "イーロン",
    "sam": "サム",
    "altman": "オルトマン",
    "satya": "サティア",
    "nadella": "ナデラ",
    "jensen": "イェンセン",
    "huang": "ファン",
    "demis": "デミス",
    "hassabis": "ハサビス",
    "marlinspike": "マーリンスパイク",
    "zuckerberg": "ッカーバーグ",
    "cook": "クック",
    "tim": "ティム",
    "bill": "ビル",
    "gates": "ゲイツ",
    "steve": "スティーブ",
    "jobs": "ジョブズ",
    "nadella": "ナデラ",

    # Tech companies
    "nvidia": "エヌビディア",
    "openai": "オープンエーアイ",
    "anthropic": "アンソロピック",
    "google": "グーグル",
    "microsoft": "マイクロソフト",
    "amazon": "アマゾン",
    "meta": "メタ",
    "apple": "アップル",
    "tesla": "テスラ",
    "spacex": "スペースエックス",
    "twitter": "ツイッター",
    "facebook": "フェイスブック",
    "instagram": "インスタグラム",
    "tiktok": "ティックトック",
    "alibaba": "アリババ",
    "tencent": "テンセント",
    "samsung": "サムスン",
    "intel": "インテル",
    "amd": "エーエムディー",
    "qualcomm": "クアルコム",
    "sony": "ソニー",
    "nintendo": "ニンテンドー",

    # Tech terms
    "emulation": "エミュレーション",
    "privacy": "プライバシー",
    "alternative": "オルタナティブ",
    "algorithm": "アルゴリズム",
    "innovation": "イノベーション",
    "generation": "ジェネレーション",
    "processing": "プロセッシング",
    "computing": "コンピューティング",
    "learning": "ラーニング",
    "neural": "ニューラル",
    "network": "ネットワーク",
    "interface": "インターフェース",
    "platform": "プラットフォーム",
    "framework": "フレームワーク",
    "database": "データベース",
    "server": "サーバー",
    "client": "クライアント",
    "browser": "ブラウザ",
    "application": "アプリケーション",
    "software": "ソフトウェア",
    "hardware": "ハードウェア",
    "security": "セキュリティ",
    "encryption": "暗号化",
    "authentication": "認証",
    "authorization": "認可",
    "virtual": "バーチャル",
    "physical": "フィジカル",
    "digital": "デジタル",
    "analog": "アナログ",
    "quantum": "クォンタム",
    "robotics": "ロボティクス",
    "automation": "オートメーション",
    "assistant": "アシスタント",
    "chatbot": "チャットボット",
    "language": "ランゲージ",
    "translation": "翻訳",
    "transcription": "文字起こし",
    "synthesis": "合成",

    # AI terms
    "artificial": "アーティフィシャル",
    "intelligence": "インテリジェンス",
    "machine": "マシン",
    "deep": "ディープ",
    "reinforcement": "強化",
    "supervised": "教師あり",
    "unsupervised": "教師なし",
    "transformer": "トランスフォーマー",
    "attention": "アテンション",
    "parameter": "パラメータ",
    "training": "トレーニング",
    "inference": "推論",
    "fine": "ファイン",
    "tuning": "チューニング",
    "prompt": "プロンプト",
    "completion": "補完",
    "token": "トークン",
    "embedding": "エンベディング",
    "vector": "ベクトル",
    "model": "モデル",
    "weights": "重み",
    "bias": "バイアス",
    "gradient": "勾配",
    "optimizer": "オプティマイザー",
    "loss": "損失",
    "accuracy": "精度",
    "precision": "適合率",
    "recall": "再現率",
    "f1": "エフワン",

    # Business terms
    "revenue": "レベニュー",
    "profit": "利益",
    "investment": "投資",
    "valuation": "評価額",
    "stock": "株",
    "share": "シェア",
    "market": "市場",
    "economy": "経済",
    "inflation": "インフレ",
    "recession": "景気後退",
    "growth": "成長",
    "decline": "低下",
    "merger": "合併",
    "acquisition": "買収",
    "partnership": "提携",
    "competition": "競争",
    "monopoly": "独占",
    "regulation": "規制",
    "policy": "政策",
    "lawsuit": "訴訟",
    "legal": "法的",
    "copyright": "著作権",
    "patent": "特許",
    "license": "ライセンス",

    # Numbers and symbols
    "fp64": "エフピーろくよん",
    "fp32": "エフピーサんに",
    "fp16": "エフピーじゅうろく",
    "int8": "イントエイト",
    "x86": "エックスはちじゅうろく",
    "arm": "アーム",
    "gpu": "ジーピーユー",
    "cpu": "シーピーユー",
    "ssd": "エスエスディー",
    "hdd": "エイチディーディー",
    "ram": "ラム",
    "rom": "ロム",
    "usb": "ユーエスビー",
    "hdmi": "エイチディーエムアイ",
    "wifi": "ワイファイ",
    "bluetooth": "ブルートゥース",
    "5g": "ファイブジー",
    "4g": "フォージー",
    "3g": "スリージー",
    "lte": "エルティーイー",
    "gsm": "ジーエスエム",
    "cdma": "シーディーマエーエム",
    "api": "エーピーアイ",
    "sdk": "エスディーケー",
    "ide": "アイディーイー",
    "ui": "ユーアイ",
    "ux": "ユーエックス",
    "vr": "ブイアール",
    "ar": "エーアール",
    "mr": "ミックスドリアリティ",
    "xr": "エックスアール",
    "iot": "アイオーティー",
    "ai": "エーアイ",
    "agi": "エージーアイ",
    "llm": "エルエルエム",
    "gpt": "ジーピーティー",
    "nlp": "エヌエルピー",
    "cv": "コンピュータービジョン",
}


# Phonetic mapping for English letters to katakana
# This is used as fallback for unknown words
PHONETIC_MAP = {
    # Consonants
    'b': 'ブ', 'c': 'ク', 'd': 'ド', 'f': 'フ', 'g': 'グ',
    'h': 'ハ', 'j': 'ジ', 'k': 'ク', 'l': 'ル', 'm': 'ム',
    'n': 'ン', 'p': 'プ', 'q': 'ク', 'r': 'ル', 's': 'ス',
    't': 'ト', 'v': 'ヴ', 'w': 'ウ', 'x': 'ク', 'y': 'イ', 'z': 'ズ',

    # Vowels
    'a': 'ア', 'e': 'エ', 'i': 'イ', 'o': 'オ', 'u': 'ウ',

    # Common combinations
    'ch': 'チ', 'sh': 'シ', 'th': 'サ', 'ph': 'フ',
    'ck': 'ック', 'ng': 'ング', 'rt': 'ルト', 'ld': 'ルド',
    'nt': 'ント', 'st': 'スト', 'sp': 'スポ', 'tr': 'トラ',
    'qu': 'ク', 'xi': 'クシ', 'xe': 'クセ',
}


def convert_english_to_katakana(text: str) -> str:
    """
    Convert English words in text to katakana for TTS pronunciation.

    Preserves Japanese text, only converts sequences of English letters.
    Single letters are kept as-is (likely acronyms handled separately).

    Args:
        text: Mixed Japanese/English text

    Returns:
        Text with English words converted to katakana
    """
    # Pattern to match English words (sequences of letters, at least 2 chars)
    # Excludes single characters which are likely part of Japanese text
    pattern = r'[a-zA-Z]{2,}'

    def replace_word(match):
        word = match.group(0)
        lower_word = word.lower()

        # Check dictionary first
        if lower_word in COMMON_WORDS:
            return COMMON_WORDS[lower_word]

        # For all-uppercase acronyms (like AI, GPU, FP64)
        if word.isupper() and len(word) <= 6:
            # Already handled by dictionary, skip
            return word

        # For capitalized words, try lowercase version
        if word[0].isupper() and len(word) <= 10:
            if lower_word in COMMON_WORDS:
                return COMMON_WORDS[lower_word]

        # Fallback: keep as-is (VOICEVOX will handle it, or add to dictionary later)
        return word

    # Replace English words with katakana equivalents
    result = re.sub(pattern, replace_word, text)

    return result


def preprocess_text_for_tts(text: str) -> str:
    """
    Preprocess text for TTS by converting English words to katakana.
    This is the main function to call from TTS modules.

    Args:
        text: Input text (may contain English words)

    Returns:
        Text with English words converted to katakana for pronunciation
    """
    return convert_english_to_katakana(text)


if __name__ == "__main__":
    # Test
    test_cases = [
        "Moxie Marlinspike created a privacy-focused alternative to ChatGPT.",
        "Nvidia's FP64 emulation is groundbreaking.",
        "Elon Musk and Sam Altman discussed AI safety.",
        "OpenAI released a new model called GPT-5.",
        "Google and Microsoft are competing in the cloud market.",
    ]

    print("=== English to Katakana Conversion Test ===\n")
    for test in test_cases:
        converted = preprocess_text_for_tts(test)
        print(f"Original: {test}")
        print(f"Converted: {converted}")
        print()
