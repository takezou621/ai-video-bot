"""
Text Normalizer - Prepares text for VOICEVOX TTS

役割:
- 数値・日付・時刻の日本語読み変換
- 特殊記号の読み変換
- HTMLエンティティのデコード

注意:
- 英単語の発音変換はVOICEVOXユーザー辞書が担当
- 本モジュールでは英単語のカタカナ変換は最小限に抑える
"""
import re
import html
from typing import List


def decode_html_entities(text: str) -> str:
    """HTMLエンティティをデコード（&#8217; → ' など）"""
    if not text:
        return text
    return html.unescape(text)


def normalize_symbols(text: str) -> str:
    """記号を読みやすい形に変換"""
    if not text:
        return text

    replacements = [
        # 記号の読み
        ("&", " アンド "),
        ("@", " アット "),
        ("#", " ハッシュ "),
        ("×", " かける "),
        ("÷", " わる "),
        ("→", " やじるし "),
        ("←", " やじるし "),
        ("↑", " やじるし "),
        ("↓", " やじるし "),
        ("※", " "),
        ("★", " "),
        ("☆", " "),
        ("●", " "),
        ("○", " "),
        ("■", " "),
        ("□", " "),
        ("▲", " "),
        ("△", " "),
        ("…", "、"),
        ("・・・", "、"),
        ("...", "、"),
        # 括弧内の英語は削除せず残す
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    # 連続スペースを1つに
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


# ============================================
# 数値・日付の日本語変換
# ============================================

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
    """整数を日本語読みに変換"""
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
    """10000未満の数値を日本語に変換"""
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
            result.append('さんぜん')
        elif count == 8:
            result.append('はっせん')
        else:
            result.append(_NUM_READINGS[str(count)] + 'せん')

    # 百 (hyaku)
    if num >= 100:
        count = num // 100
        num %= 100
        if count == 1:
            result.append('ひゃく')
        elif count == 3:
            result.append('さんびゃく')
        elif count == 6:
            result.append('ろっぴゃく')
        elif count == 8:
            result.append('はっぴゃく')
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
    """日付を日本語に変換"""
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
    """時刻を日本語に変換"""
    # HH:MM:SS
    def replace_time_hms(m):
        h, m_val, s = m.groups()
        return f'{int(h)}時{int(m_val)}分{int(s)}秒'

    text = re.sub(r'(\d{1,2}):(\d{2}):(\d{2})', replace_time_hms, text)

    # HH:MM（タイムスタンプ以外）
    def replace_time_hm(m):
        h, m_val = m.groups()
        return f'{int(h)}時{int(m_val)}分'

    text = re.sub(r'(?<![(\d])(\d{1,2}):(\d{2})(?![)\d:])', replace_time_hm, text)

    return text


def _normalize_percentages(text: str) -> str:
    """パーセントを日本語に変換"""
    def replace_pct(m):
        num = m.group(1).replace(',', '')
        if '.' in num:
            int_part, dec_part = num.split('.')
            return f'{_number_to_japanese(int(int_part))}点{_number_to_japanese(int(dec_part))}パーセント'
        return f'{_number_to_japanese(int(num))}パーセント'

    text = re.sub(r'(\d[\d,.]*)%', replace_pct, text)
    return text


def _normalize_currency(text: str) -> str:
    """通貨を日本語に変換"""
    # $X.XX
    def replace_dollar(m):
        num = m.group(1).replace(',', '')
        if '.' in num:
            parts = num.split('.')
            int_part = _number_to_japanese(int(parts[0])) if parts[0] else 'ゼロ'
            dec_part = _number_to_japanese(int(parts[1])) if parts[1] else 'ゼロ'
            return f'{int_part}ドル{dec_part}セント'
        return f'{_number_to_japanese(int(num))}ドル'

    text = re.sub(r'\$(\d[\d,.]*)', replace_dollar, text)

    # ¥X,XXX
    def replace_yen(m):
        num = m.group(1).replace(',', '')
        return f'{_number_to_japanese(int(num))}円'

    text = re.sub(r'[¥￥](\d[\d,]*)', replace_yen, text)

    return text


def _normalize_large_numbers(text: str) -> str:
    """大きな数値（億、兆など）を日本語に変換"""
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
    """バージョン番号を日本語に変換（GPT-4.5 → GPT-4点5）"""
    def replace_version(m):
        major, minor = m.groups()
        return f'{major}点{minor}'

    text = re.sub(r'(\d+)\.(\d+)(?=\s|$|[^\d])', replace_version, text)

    return text


def normalize_for_tts(text: str) -> str:
    """
    TTS用にテキストを正規化（メイン関数）

    処理内容:
    1. HTMLエンティティのデコード
    2. 日付・時刻の変換
    3. 通貨・パーセントの変換
    4. 大きな数値の変換
    5. 記号の変換
    """
    if not text:
        return text

    # Step 1: HTMLエンティティをデコード
    text = decode_html_entities(text)

    # Step 2: 数値・日付系の変換（順序が重要）
    text = _normalize_dates(text)
    text = _normalize_times(text)
    text = _normalize_currency(text)
    text = _normalize_percentages(text)
    text = _normalize_large_numbers(text)
    text = _normalize_model_versions(text)

    # Step 3: 記号の変換
    text = normalize_symbols(text)

    return text


# ============================================
# テキスト分割（長文対応）
# ============================================

def split_into_chunks(text: str, max_chars: int = 80, min_chars: int = 20) -> List[str]:
    """
    テキストをTTS用のチャンクに分割

    Args:
        text: 分割するテキスト
        max_chars: チャンクの最大文字数
        min_chars: チャンクの最小文字数

    Returns:
        テキストチャンクのリスト
    """
    if not text or len(text) <= max_chars:
        return [text] if text else []

    chunks = []
    remaining = text.strip()

    # 分割優先度（順に試行）
    split_patterns = [
        r'。',  # 句点
        r'！',  # 感嘆符
        r'？',  # 疑問符
        r'、',  # 読点
        r'）',  # 閉じ括弧
        r'」',  # 閉じ鉤括弧
        r'\n',  # 改行
        r'　',  # 全角スペース
        r' ',   # 半角スペース
    ]

    while len(remaining) > max_chars:
        best_split = -1

        for pattern in split_patterns:
            for i in range(min(max_chars, len(remaining)), min_chars - 1, -1):
                if re.match(pattern, remaining[i-1:i]):
                    best_split = i
                    break
            if best_split > 0:
                break

        if best_split <= 0:
            best_split = max_chars

        chunk = remaining[:best_split].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[best_split:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


# ============================================
# 後方互換性のためのエイリアス
# ============================================

def normalize_for_tts_advanced(text: str) -> str:
    """後方互換性のためのエイリアス"""
    return normalize_for_tts(text)


def normalize_text_for_tts(text: str) -> str:
    """
    後方互換性のためのエイリアス

    注意: 英単語のカタカナ変換はVOICEVOXユーザー辞書が担当するため、
    この関数では英単語の変換を行わない。
    """
    return text  # 変換せずそのまま返す


def normalize_and_chunk(text: str, max_chars: int = 80) -> List[str]:
    """正規化と分割を一括実行"""
    text = normalize_for_tts(text)
    return split_into_chunks(text, max_chars=max_chars)


if __name__ == "__main__":
    print("=== Text Normalizer Test ===\n")

    test_cases = [
        "2024/01/15のニュースです。",
        "価格は$99.99です。",
        "売上が150億円を突破しました。",
        "成長率は25.5%でした。",
        "会議は14:30から開始です。",
        "GPT-4.5がリリースされました。",
        "詳細はURL→こちらをご覧ください。",
    ]

    for text in test_cases:
        result = normalize_for_tts(text)
        print(f"入力: {text}")
        print(f"出力: {result}")
        print("-" * 40)
