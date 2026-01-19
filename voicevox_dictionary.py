"""
VOICEVOX User Dictionary Manager

VOICEVOXが正しく発音できない単語のみをユーザー辞書に登録する。
VOICEVOXが既に正しく発音できる単語（YouTube, iPhone, Google等）は登録不要。

使用方法:
    from voicevox_dictionary import ensure_dictionary_initialized
    ensure_dictionary_initialized()  # 起動時に1回呼び出し
"""
import os
import requests
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://voicevox:50021")

# 辞書が初期化済みかどうか
_initialized = False


@dataclass
class DictionaryEntry:
    """ユーザー辞書エントリ"""
    surface: str          # 表層形（元の単語）
    pronunciation: str    # 発音（カタカナ）
    accent_type: int      # アクセント型（音が下がる位置）
    word_type: str = "PROPER_NOUN"  # 品詞
    priority: int = 9     # 優先度（1-9、大きいほど優先）


# VOICEVOXが正しく発音できない単語のみを登録
# 注: YouTube, iPhone, NVIDIA, Twitter, Google, Microsoft, Amazon等は
#     VOICEVOXがネイティブで正しく発音するため登録不要
ESSENTIAL_DICTIONARY: List[DictionaryEntry] = [
    # ============================================
    # アルファベット頭字語（VOICEVOXがアルファベット読みしてしまう）
    # ============================================
    # AI関連
    DictionaryEntry("AI", "エーアイ", 3),
    DictionaryEntry("AGI", "エージーアイ", 5),
    DictionaryEntry("LLM", "エルエルエム", 5),
    DictionaryEntry("GPT", "ジーピーティー", 5),
    DictionaryEntry("ChatGPT", "チャットジーピーティー", 7),
    DictionaryEntry("GPT-4", "ジーピーティーフォー", 7),
    DictionaryEntry("GPT-5", "ジーピーティーファイブ", 7),
    DictionaryEntry("RAG", "ラグ", 1),

    # クラウド・インフラ
    DictionaryEntry("API", "エーピーアイ", 5),
    DictionaryEntry("AWS", "エーダブリューエス", 7),
    DictionaryEntry("GCP", "ジーシーピー", 5),
    DictionaryEntry("GPU", "ジーピーユー", 5),
    DictionaryEntry("CPU", "シーピーユー", 5),
    DictionaryEntry("SaaS", "サース", 2),
    DictionaryEntry("PaaS", "パース", 2),
    DictionaryEntry("IaaS", "イアース", 3),

    # 役職
    DictionaryEntry("CEO", "シーイーオー", 5),
    DictionaryEntry("CTO", "シーティーオー", 5),
    DictionaryEntry("CFO", "シーエフオー", 5),

    # 技術用語
    DictionaryEntry("IoT", "アイオーティー", 5),
    DictionaryEntry("VR", "ブイアール", 4),
    DictionaryEntry("AR", "エーアール", 4),
    DictionaryEntry("NFT", "エヌエフティー", 5),
    DictionaryEntry("URL", "ユーアールエル", 5),
    DictionaryEntry("USB", "ユーエスビー", 5),
    DictionaryEntry("SSD", "エスエスディー", 5),
    DictionaryEntry("HDD", "エイチディーディー", 7),
    DictionaryEntry("SQL", "エスキューエル", 5),
    DictionaryEntry("HTML", "エイチティーエムエル", 7),
    DictionaryEntry("CSS", "シーエスエス", 5),
    DictionaryEntry("JSON", "ジェイソン", 4),
    DictionaryEntry("XML", "エックスエムエル", 5),
    DictionaryEntry("PDF", "ピーディーエフ", 5),
    DictionaryEntry("OS", "オーエス", 3),
    DictionaryEntry("UI", "ユーアイ", 3),
    DictionaryEntry("UX", "ユーエックス", 4),
    DictionaryEntry("SEO", "エスイーオー", 5),
    DictionaryEntry("SNS", "エスエヌエス", 5),

    # ============================================
    # 複合語・略語（VOICEVOXが誤読する）
    # ============================================
    DictionaryEntry("Gmail", "ジーメール", 3),
    DictionaryEntry("iPhone", "アイフォーン", 4),  # 念のため登録
    DictionaryEntry("iPad", "アイパッド", 4),
    DictionaryEntry("macOS", "マックオーエス", 5),
    DictionaryEntry("iOS", "アイオーエス", 5),
    DictionaryEntry("GitHub", "ギットハブ", 4),
    DictionaryEntry("GitLab", "ギットラブ", 4),
    DictionaryEntry("VSCode", "ブイエスコード", 5),
    DictionaryEntry("VS Code", "ブイエスコード", 5),
    DictionaryEntry("TypeScript", "タイプスクリプト", 6),
    DictionaryEntry("JavaScript", "ジャバスクリプト", 6),
    DictionaryEntry("Node.js", "ノードジェーエス", 6),
    DictionaryEntry("Vue.js", "ビュージェーエス", 6),
    DictionaryEntry("Next.js", "ネクストジェーエス", 7),
    DictionaryEntry("React", "リアクト", 3),
    DictionaryEntry("Docker", "ドッカー", 3),
    DictionaryEntry("Kubernetes", "クバネティス", 5),
    DictionaryEntry("Wi-Fi", "ワイファイ", 4),
    DictionaryEntry("WiFi", "ワイファイ", 4),
    DictionaryEntry("Bluetooth", "ブルートゥース", 5),

    # ============================================
    # AIサービス・モデル名
    # ============================================
    DictionaryEntry("Claude", "クロード", 3),
    DictionaryEntry("Gemini", "ジェミニ", 3),
    DictionaryEntry("Copilot", "コパイロット", 4),
    DictionaryEntry("DALL-E", "ダリー", 2),
    DictionaryEntry("Whisper", "ウィスパー", 4),
    DictionaryEntry("Midjourney", "ミッドジャーニー", 6),
    DictionaryEntry("Stable Diffusion", "ステーブルディフュージョン", 9),
    DictionaryEntry("LLaMA", "ラマ", 2),
    DictionaryEntry("Llama", "ラマ", 2),
    DictionaryEntry("Mistral", "ミストラル", 4),
    DictionaryEntry("Anthropic", "アンソロピック", 5),
    DictionaryEntry("OpenAI", "オープンエーアイ", 6),
    DictionaryEntry("DeepMind", "ディープマインド", 5),
    DictionaryEntry("Hugging Face", "ハギングフェイス", 5),
    DictionaryEntry("HuggingFace", "ハギングフェイス", 5),

    # ============================================
    # その他よく使われる略語
    # ============================================
    DictionaryEntry("FAQ", "エフエーキュー", 5),
    DictionaryEntry("DIY", "ディーアイワイ", 5),
    DictionaryEntry("B2B", "ビーツービー", 5),
    DictionaryEntry("B2C", "ビーツーシー", 5),
    DictionaryEntry("KPI", "ケーピーアイ", 5),
    DictionaryEntry("ROI", "アールオーアイ", 5),
    DictionaryEntry("MVP", "エムブイピー", 5),
    DictionaryEntry("PoC", "ピーオーシー", 5),
    DictionaryEntry("OKR", "オーケーアール", 5),

    # ============================================
    # 英単語・人名（VOICEVOXがカタカナ読みしてしまう）
    # ============================================
    # 人名
    DictionaryEntry("Moxie", "モキシー", 3),
    DictionaryEntry("Moxie Marlinspike", "モキシーマーリンスパイク", 7),
    DictionaryEntry("Marlinspike", "マーリンスパイク", 5),
    DictionaryEntry("Musk", "マスク", 2),
    DictionaryEntry("Elon Musk", "イーロンマスク", 5),
    DictionaryEntry("Sam Altman", "サムオルトマン", 5),
    DictionaryEntry("Altman", "オルトマン", 4),
    DictionaryEntry("Satya", "サティア", 3),
    DictionaryEntry("Nadella", "ナデラ", 3),
    DictionaryEntry("Jensen", "イェンセン", 3),
    DictionaryEntry("Huang", "ファン", 2),
    DictionaryEntry("Demis", "デミス", 3),
    DictionaryEntry("Hassabis", "ハサビス", 4),

    # 技術用語（英単語）
    DictionaryEntry("FP64", "エフピーろくよん", 5),
    DictionaryEntry("FP32", "エフピーサんに", 5),
    DictionaryEntry("FP16", "エフピーじゅうろく", 5),
    DictionaryEntry("int8", "イントエイト", 4),
    DictionaryEntry("emulation", "エミュレーション", 5),
    DictionaryEntry("privacy", "プライバシー", 4),
    DictionaryEntry("alternative", "オルタナティブ", 6),
    DictionaryEntry("algorithm", "アルゴリズム", 5),
    DictionaryEntry("innovation", "イノベーション", 5),
]

# マッチング専用辞書（VOICEVOX登録は不要だが、Whisperとの照合用に読みが必要な単語）
# 例: Google -> グーグル (Whisper出力) vs Google (スクリプト)
MATCHING_ONLY_DICTIONARY: List[DictionaryEntry] = [
    DictionaryEntry("Google", "グーグル", 1),
    DictionaryEntry("YouTube", "ユーチューブ", 4),
    DictionaryEntry("Amazon", "アマゾン", 2),
    DictionaryEntry("Microsoft", "マイクロソフト", 4),
    DictionaryEntry("Facebook", "フェイスブック", 4),
    DictionaryEntry("Apple", "アップル", 1),
    DictionaryEntry("Netflix", "ネットフリックス", 4),
    DictionaryEntry("Twitter", "ツイッター", 4),
    DictionaryEntry("X", "エックス", 1),
    DictionaryEntry("Instagram", "インスタグラム", 4),
    DictionaryEntry("TikTok", "ティックトック", 4),
    DictionaryEntry("NVIDIA", "エヌビディア", 4),
    DictionaryEntry("Windows", "ウィンドウズ", 4),
    DictionaryEntry("Mac", "マック", 1),
    DictionaryEntry("Linux", "リナックス", 1),
    DictionaryEntry("Android", "アンドロイド", 4),
    DictionaryEntry("iOS", "アイオーエス", 5),
    DictionaryEntry("Chrome", "クローム", 2),
    DictionaryEntry("Safari", "サファリ", 2),
    DictionaryEntry("Edge", "エッジ", 1),
    DictionaryEntry("Firefox", "ファイアーフォックス", 4),
    DictionaryEntry("Python", "パイソン", 1),
    DictionaryEntry("Java", "ジャバ", 1),
    DictionaryEntry("Ruby", "ルビー", 1),
    DictionaryEntry("PHP", "ピーエイチピー", 5),
    DictionaryEntry("Go", "ゴー", 1),
    DictionaryEntry("Rust", "ラスト", 1),
    DictionaryEntry("Swift", "スイフト", 1),
    DictionaryEntry("Kotlin", "コトリン", 1),
    DictionaryEntry("TypeScript", "タイプスクリプト", 4),
    DictionaryEntry("Docker", "ドッカー", 1),
    DictionaryEntry("Kubernetes", "クバネティス", 4),
    DictionaryEntry("AWS", "エーダブリューエス", 7),
    DictionaryEntry("Azure", "アジュール", 2),
    DictionaryEntry("GCP", "ジーシーピー", 5),
]


def get_current_dictionary() -> Dict:
    """現在のユーザー辞書を取得"""
    try:
        resp = requests.get(f"{VOICEVOX_URL}/user_dict", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"[VOICEVOX Dict] Failed to get dictionary: {e}")
    return {}


def add_word(entry: DictionaryEntry) -> Optional[str]:
    """単語をユーザー辞書に追加（UUIDを返す）"""
    try:
        resp = requests.post(
            f"{VOICEVOX_URL}/user_dict_word",
            params={
                "surface": entry.surface,
                "pronunciation": entry.pronunciation,
                "accent_type": entry.accent_type,
                "word_type": entry.word_type,
                "priority": entry.priority,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()  # UUID
    except Exception as e:
        print(f"[VOICEVOX Dict] Failed to add '{entry.surface}': {e}")
    return None


def delete_word(word_uuid: str) -> bool:
    """単語をユーザー辞書から削除"""
    try:
        resp = requests.delete(
            f"{VOICEVOX_URL}/user_dict_word/{word_uuid}",
            timeout=10,
        )
        return resp.status_code == 204
    except Exception as e:
        print(f"[VOICEVOX Dict] Failed to delete {word_uuid}: {e}")
    return False


def clear_dictionary() -> int:
    """ユーザー辞書をクリア（削除した件数を返す）"""
    current = get_current_dictionary()
    deleted = 0
    for uuid in current.keys():
        if delete_word(uuid):
            deleted += 1
    return deleted


def initialize_dictionary(force: bool = False) -> Tuple[int, int]:
    """
    必須単語をユーザー辞書に登録

    Args:
        force: Trueの場合、既存の辞書をクリアして再登録

    Returns:
        (追加した件数, スキップした件数)
    """
    global _initialized

    if _initialized and not force:
        return (0, 0)

    current = get_current_dictionary()

    # 既存のsurfaceを抽出（全角・半角を正規化）
    existing_surfaces = set()
    for entry in current.values():
        surface = entry.get("surface", "")
        # 全角→半角変換して比較用に正規化
        normalized = surface.translate(str.maketrans(
            "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        ))
        existing_surfaces.add(normalized.lower())

    added = 0
    skipped = 0

    for entry in ESSENTIAL_DICTIONARY:
        # Generate variations: Original, UPPERCASE, lowercase, Full-width UPPERCASE
        # Full-width uppercase is needed for TTS preprocessing which converts all letters to full-width uppercase
        def to_fullwidth_uppercase(s: str) -> str:
            result = []
            for char in s:
                if 'a' <= char <= 'z':
                    result.append(chr(ord(char) - ord('a') + ord('Ａ')))
                elif 'A' <= char <= 'Z':
                    result.append(chr(ord(char) - ord('A') + ord('Ａ')))
                else:
                    result.append(char)
            return ''.join(result)

        surface_upper = entry.surface.upper()
        variations = {
            entry.surface,
            surface_upper,
            entry.surface.lower(),
            to_fullwidth_uppercase(surface_upper),  # Full-width uppercase for TTS matching
        }

        for surface in variations:
            # Check if this variation is already registered
            # For full-width variations, check exact match first (to allow both titlecase and uppercase)
            if any(c in 'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ' for c in surface):
                # Full-width entry - check if exact string is already registered
                if surface in existing_surfaces:
                    continue
            else:
                # Half-width entry - normalize to check
                normalized = surface.translate(str.maketrans(
                    "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９",
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
                ))
                if normalized.lower() in existing_surfaces:
                    continue

            # Mark this surface as registered (for both full-width and normalized)
            if any(c in 'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ' for c in surface):
                existing_surfaces.add(surface)  # Full-width: add exact string
            else:
                normalized = surface.translate(str.maketrans(
                    "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９",
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
                ))
                existing_surfaces.add(normalized.lower())

            # Create entry with this surface
            new_entry = DictionaryEntry(
                surface=surface,
                pronunciation=entry.pronunciation,
                accent_type=entry.accent_type,
                word_type=entry.word_type,
                priority=entry.priority
            )

            # Register
            uuid = add_word(new_entry)
            if uuid:
                added += 1
                # Mark as registered to avoid re-adding same lower-normalized word in this loop
                existing_surfaces.add(surface.lower())
            else:
                skipped += 1  # Failed or skipped

    _initialized = True

    if added > 0:
        print(f"[VOICEVOX Dict] Initialized: {added} added, {skipped} skipped")

    return (added, skipped)


def ensure_dictionary_initialized():
    """辞書が初期化されていることを確認（起動時に呼び出す）"""
    global _initialized
    if not _initialized:
        initialize_dictionary()


def check_pronunciation(text: str, speaker_id: int = 20) -> str:
    """テキストの発音を確認（デバッグ用）"""
    try:
        resp = requests.post(
            f"{VOICEVOX_URL}/audio_query",
            params={"text": text, "speaker": speaker_id},
            timeout=10,
        )
        data = resp.json()
        accent_phrases = data.get("accent_phrases", [])
        reading = ""
        for phrase in accent_phrases:
            moras = phrase.get("moras", [])
            reading += "".join([m.get("text", "") for m in moras])
        return reading
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    print("=== VOICEVOX User Dictionary Manager ===\n")

    # 現在の辞書を表示
    current = get_current_dictionary()
    print(f"Current dictionary: {len(current)} entries")

    # 辞書を初期化
    print("\nInitializing dictionary...")
    added, skipped = initialize_dictionary(force=False)
    print(f"Added: {added}, Skipped: {skipped}")

    # テスト
    print("\n=== Pronunciation Test ===")
    test_words = ["Gmail", "ChatGPT", "API", "YouTube", "iPhone", "Google"]
    for word in test_words:
        reading = check_pronunciation(word)
        print(f"  {word:15} → {reading}")
