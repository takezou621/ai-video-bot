"""
Podcast API Client - 外部APIからポッドキャストシナリオとタイトルを取得
https://pg-admin.takezou.com/api/podcasts からデータを取得し、
Host A/Host Bを固定のホスト名に変換
"""
import os
import re
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, date

# API設定
PODCAST_API_URL = os.getenv(
    "PODCAST_API_URL",
    "https://pg-admin.takezou.com/api/podcasts"
)
PODCAST_API_ENABLED = os.getenv("PODCAST_API_ENABLED", "true").lower() == "true"

# ホスト名の設定 (Host A → 男性, Host B → 女性)
# これらの名前は動画内で表示されます
HOST_A_NAME = "田中太郎"
HOST_B_NAME = "佐藤花子"
def fetch_podcasts(limit: int = 5, order: str = "id.desc") -> List[Dict[str, Any]]:
    """
    APIからポッドキャストデータを取得

    Args:
        limit: 取得する件数
        order: 並び順（デフォルトはID降順）

    Returns:
        ポッドキャストデータのリスト
    """
    try:
        params = {
            "order": order,
            "limit": limit
        }
        response = requests.get(PODCAST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[PodcastAPI] Error fetching podcasts: {e}")
        raise


def fetch_podcast_by_date(target_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    指定日付のポッドキャストデータを取得

    Args:
        target_date: 取得する日付（YYYY-MM-DD形式、省略時は当日）

    Returns:
        マッチするポッドキャストデータ、なければNone
    """
    if target_date is None:
        target_date = date.today().isoformat()

    try:
        # 日付でフィルタリング
        params = {
            "date": f"eq.{target_date}T00:00:00",
            "limit": 1
        }
        response = requests.get(PODCAST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data:
            return data[0]

        # 日付フィルタでヒットしない場合は最新を取得
        print(f"[PodcastAPI] No podcast found for date {target_date}, fetching latest...")
        podcasts = fetch_podcasts(limit=5)
        if podcasts:
            # 日付が近いものを探す
            for podcast in podcasts:
                podcast_date = podcast.get("date", "")[:10]
                if podcast_date == target_date:
                    return podcast
            # 見つからなければ最新を返す
            return podcasts[0]

        return None

    except requests.RequestException as e:
        print(f"[PodcastAPI] Error fetching podcast by date: {e}")
        raise


def parse_podcast_scenario(scenario_text: str) -> List[Dict[str, str]]:
    """
    シナリオをdialogues配列に変換
    対応形式:
    - Host A: xxx / Host B: yyy
    - 名前付きホスト (例: Amano Yui: xxx / Morishita Nana: yyy)

    Args:
        scenario_text: シナリオテキスト

    Returns:
        [{"speaker": "男性", "text": "こんにちは"}, {"speaker": "女性", "text": "はい..."}]
    """
    dialogues = []

    if not scenario_text:
        return dialogues

    # まずHost A/B形式を試す
    dialogues = _parse_host_ab_format(scenario_text)

    # Host A/B形式で見つからなければ、名前付きホスト形式を試す
    if not dialogues:
        dialogues = _parse_named_host_format(scenario_text)

    return dialogues


def _parse_host_ab_format(scenario_text: str) -> List[Dict[str, str]]:
    """Host A: / Host B: 形式をパース"""
    dialogues = []

    pattern = r'Host\s+([AB]):\s*'
    parts = re.split(pattern, scenario_text.strip())

    i = 0
    while i < len(parts) and not parts[i].strip():
        i += 1
    while i < len(parts) and parts[i] not in ["A", "B"]:
        i += 1

    while i < len(parts) - 1:
        speaker_id = parts[i].strip()
        text_part = parts[i + 1].strip() if i + 1 < len(parts) else ""

        text_lines = []
        for line in text_part.split('\n'):
            line = line.strip()
            if re.match(r'^\d+\.\s+', line):
                continue
            if re.match(r'^\(\d+:\d+\)', line):
                continue
            if re.match(r'^【.*】', line):
                continue
            if re.match(r'^Today\'s date:', line):
                continue
            if line:
                text_lines.append(line)

        text = ' '.join(text_lines).strip()

        if speaker_id in ["A", "B"] and text:
            speaker = "男性" if speaker_id == "A" else "女性"
            dialogues.append({
                "speaker": speaker,
                "text": text
            })

        i += 2

    return dialogues


def _parse_named_host_format(scenario_text: str) -> List[Dict[str, str]]:
    """
    名前付きホスト形式をパース
    例: "Amano Yui: テキスト" や "森下奈々: テキスト"
    最初に登場したホストを男性、2番目を女性として扱う
    """
    dialogues = []

    # 名前: テキスト のパターン（英語名または日本語名）
    # 名前は2-20文字程度、コロンの後にテキストが続く
    pattern = r'\n?([A-Za-z][A-Za-z\s]{1,30}|[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]{2,10}):\s*'

    parts = re.split(pattern, scenario_text.strip())

    # ホスト名を収集（出現順）
    host_names = []
    host_to_speaker = {}

    i = 0
    while i < len(parts) - 1:
        part = parts[i].strip()

        # タイムスタンプや日付などをスキップ
        if re.match(r'^\(\d+:\d+', part):
            i += 1
            continue
        if re.match(r'^Today\'s date', part):
            i += 1
            continue
        if re.match(r'^\d{4}年', part):
            i += 1
            continue

        # 有効なホスト名かチェック
        if re.match(r'^[A-Za-z][A-Za-z\s]{1,30}$', part) or re.match(r'^[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]{2,10}$', part):
            host_name = part
            text_part = parts[i + 1].strip() if i + 1 < len(parts) else ""

            # 新しいホスト名を登録
            if host_name not in host_to_speaker:
                if len(host_names) == 0:
                    host_to_speaker[host_name] = "男性"
                else:
                    host_to_speaker[host_name] = "女性"
                host_names.append(host_name)

            # テキストをクリーンアップ
            text_lines = []
            for line in text_part.split('\n'):
                line = line.strip()
                if re.match(r'^\(\d+:\d+\)', line):
                    continue
                if re.match(r'^\d+\.\s+', line):
                    continue
                if re.match(r'^【.*】', line):
                    continue
                if re.match(r'^\d{4}年\d+月\d+日', line):
                    continue
                if line:
                    text_lines.append(line)

            text = ' '.join(text_lines).strip()
            # テキスト先頭のタイムスタンプや日付を除去
            text = re.sub(r'^[\d年月日\s/:\(\)]+\s*', '', text).strip()

            if text:
                dialogues.append({
                    "speaker": host_to_speaker[host_name],
                    "text": text
                })

            i += 2
        else:
            i += 1

    return dialogues


def get_pending_podcasts(
    date_filter: Optional[str] = None,
    status_filter: str = "todo"
) -> List[Dict[str, Any]]:
    """
    処理待ち（status=todo）のポッドキャストを取得

    Args:
        date_filter: 日付フィルタ（YYYY-MM-DD形式）
        status_filter: ステータスフィルタ（デフォルトはtodo）

    Returns:
        処理待ちポッドキャストのリスト
    """
    try:
        params = {
            "status": f"eq.{status_filter}",
            "order": "id.desc",
            "limit": 10
        }

        if date_filter:
            params["date"] = f"eq.{date_filter}T00:00:00"

        response = requests.get(PODCAST_API_URL, params=params, timeout=30)
        response.raise_for_status()
        podcasts = response.json()

        result = []
        for podcast in podcasts:
            dialogues = parse_podcast_scenario(podcast.get("podcast_scenario", ""))
            if not dialogues:
                print(f"[PodcastAPI] Warning: Podcast id={podcast.get('id')} has no valid dialogues")
                continue

            result.append({
                "id": podcast.get("id"),
                "date": podcast.get("date", "")[:10],
                "youtube_title": podcast.get("youtube_title", ""),
                "summary": podcast.get("summary", ""),
                "scenario": podcast.get("podcast_scenario", ""),
                "status": podcast.get("status", ""),
                "dialogues": dialogues,
                "thumbnail_image_path": podcast.get("thumbnail_image_path", ""),
                "background_image_path": podcast.get("background_image_path", "")
            })

        print(f"[PodcastAPI] Found {len(result)} pending podcast(s)")
        return result

    except requests.RequestException as e:
        print(f"[PodcastAPI] Error fetching pending podcasts: {e}")
        raise


def create_script_from_podcast(podcast_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    APIから取得したポッドキャストデータをscript.json形式に変換

    Args:
        podcast_data: get_pending_podcasts()が返すデータ

    Returns:
        script.json形式のデータ
        {
            "title": "...",
            "dialogues": [...],
            "summary": "...",
            "thumbnail_text": "...",
            "host_names": {"male": "田中太郎", "female": "佐藤花子"}
        }
    """
    youtube_title = podcast_data.get("youtube_title", "")

    return {
        "title": youtube_title,
        "dialogues": podcast_data.get("dialogues", []),
        "summary": podcast_data.get("summary", ""),
        "description": podcast_data.get("summary", ""),
        "thumbnail_text": youtube_title[:20] if youtube_title else "",
        "source": "podcast_api",
        "podcast_id": podcast_data.get("id"),
        "host_names": {
            "male": HOST_A_NAME,
            "female": HOST_B_NAME
        },
        "tags": ["AI", "ニュース", "テクノロジー", "最新", "解説"]
    }


def update_podcast_status(
    podcast_id: int,
    status: str = "done"
) -> bool:
    """
    ポッドキャストのステータスを更新

    Args:
        podcast_id: ポッドキャストID
        status: 新しいステータス（done/error/processing）

    Returns:
        成功時True
    """
    try:
        url = f"{PODCAST_API_URL}?id=eq.{podcast_id}"
        payload = {"status": status}
        headers = {"Content-Type": "application/json", "Prefer": "return=minimal"}

        response = requests.patch(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        print(f"[PodcastAPI] Updated podcast {podcast_id} status to '{status}'")
        return True

    except requests.RequestException as e:
        print(f"[PodcastAPI] Error updating podcast status: {e}")
        return False


def is_podcast_api_enabled() -> bool:
    """
    Podcast API入力が有効かどうか

    Returns:
        PODCAST_API_ENABLED が true の場合 True
    """
    return PODCAST_API_ENABLED


def get_today_podcast() -> Optional[Dict[str, Any]]:
    """
    当日のポッドキャストを取得

    Returns:
        当日のポッドキャストデータ、なければNone
    """
    today = date.today().isoformat()
    pending = get_pending_podcasts(date_filter=today)
    return pending[0] if pending else None


# テスト用
if __name__ == "__main__":
    print("=== Podcast API Client Test ===\n")

    print("Fetching latest podcasts...")
    try:
        podcasts = fetch_podcasts(limit=3)
        print(f"Found {len(podcasts)} podcasts\n")

        for podcast in podcasts:
            print(f"ID: {podcast.get('id')}")
            print(f"Date: {podcast.get('date', '')[:10]}")
            print(f"Title: {podcast.get('youtube_title', '')[:50]}...")
            print(f"Status: {podcast.get('status')}")

            # シナリオをパース
            dialogues = parse_podcast_scenario(podcast.get('podcast_scenario', ''))
            print(f"Dialogues: {len(dialogues)} exchanges")

            if dialogues:
                print(f"  First: {dialogues[0]['speaker']}: {dialogues[0]['text'][:50]}...")
                print(f"  Last: {dialogues[-1]['speaker']}: {dialogues[-1]['text'][:50]}...")

            print("-" * 50)

        # スクリプト形式に変換テスト
        if podcasts:
            print("\n=== Script Conversion Test ===")
            pending = get_pending_podcasts()
            if pending:
                script = create_script_from_podcast(pending[0])
                print(f"Title: {script['title'][:50]}...")
                print(f"Host names: {script['host_names']}")
                print(f"Dialogues: {len(script['dialogues'])} exchanges")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
