"""
Google Sheets Input Reader - スプレッドシートから動画生成データを読み込み
Service Account認証を使用してスプレッドシートからシナリオ、タイトル等を取得
"""
import os
import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Google API imports
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("[SheetsReader] Warning: google-api-python-client not installed")

# Environment variables
SHEETS_INPUT_ENABLED = os.getenv("SHEETS_INPUT_ENABLED", "false").lower() == "true"
SHEETS_SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID", "")
SHEETS_SERVICE_ACCOUNT_FILE = os.getenv("SHEETS_SERVICE_ACCOUNT_FILE", "service_account.json")
SHEETS_RANGE = os.getenv("SHEETS_RANGE", "シート1!A:E")

# Scopes for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_sheets_service():
    """
    Service Account認証でGoogle Sheets APIサービスを取得

    Returns:
        Google Sheets API service object
    """
    if not GOOGLE_API_AVAILABLE:
        raise RuntimeError("google-api-python-client is not installed")

    service_account_path = Path(SHEETS_SERVICE_ACCOUNT_FILE)
    if not service_account_path.exists():
        raise FileNotFoundError(
            f"Service Account file not found: {SHEETS_SERVICE_ACCOUNT_FILE}\n"
            "Please download the JSON key from Google Cloud Console"
        )

    credentials = Credentials.from_service_account_file(
        str(service_account_path),
        scopes=SCOPES
    )

    service = build('sheets', 'v4', credentials=credentials)
    return service


def parse_scenario_text(scenario_text: str) -> List[Dict[str, str]]:
    """
    A: xxx B: yyy 形式のシナリオテキストを dialogues 配列に変換

    Args:
        scenario_text: "A: こんにちは B: はい、今日は..." 形式のテキスト

    Returns:
        [{"speaker": "A", "text": "こんにちは"}, {"speaker": "B", "text": "はい、今日は..."}]
    """
    dialogues = []

    if not scenario_text:
        return dialogues

    # パターン: "A:" または "B:" で始まるセグメントを分割
    # 改行やスペースを含む可能性があるので柔軟に対応
    pattern = r'([AB]):\s*'

    # テキストを分割
    parts = re.split(pattern, scenario_text.strip())

    # 最初の空要素をスキップ
    if parts and not parts[0].strip():
        parts = parts[1:]

    # ペアで処理 (speaker, text, speaker, text, ...)
    i = 0
    while i < len(parts) - 1:
        speaker = parts[i].strip()
        text = parts[i + 1].strip() if i + 1 < len(parts) else ""

        if speaker in ["A", "B"] and text:
            dialogues.append({
                "speaker": speaker,
                "text": text
            })

        i += 2

    return dialogues


def get_pending_rows(
    spreadsheet_id: Optional[str] = None,
    sheet_range: Optional[str] = None,
    date_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    スプレッドシートから処理待ちの行を取得

    Args:
        spreadsheet_id: スプレッドシートID (省略時は環境変数から)
        sheet_range: 読み取り範囲 (省略時は環境変数から)
        date_filter: 特定の日付のみ取得 (YYYY-MM-DD形式、省略時は全てのpending)

    Returns:
        処理待ち行のリスト
        [
            {
                "row_index": 2,
                "date": "2024-12-23",
                "scenario": "A: こんにちは B: ...",
                "summary": "概要テキスト",
                "youtube_title": "タイトル",
                "status": "pending",
                "dialogues": [{"speaker": "A", "text": "..."}]
            }
        ]
    """
    spreadsheet_id = spreadsheet_id or SHEETS_SPREADSHEET_ID
    sheet_range = sheet_range or SHEETS_RANGE

    if not spreadsheet_id:
        raise ValueError("SHEETS_SPREADSHEET_ID is not set")

    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()

        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=sheet_range
        ).execute()

        rows = result.get('values', [])

        if not rows:
            print("[SheetsReader] No data found in spreadsheet")
            return []

        # ヘッダー行をスキップ (1行目)
        pending_rows = []
        for idx, row in enumerate(rows[1:], start=2):  # row_index は2から開始 (1行目はヘッダー)
            # 列: A=Date, B=Scenario, C=Summary, D=Title, E=?, F=?, G=Status
            if len(row) < 4:
                continue  # 必要な列が足りない行はスキップ

            date_val = row[0].strip() if len(row) > 0 else ""
            scenario = row[1].strip() if len(row) > 1 else ""
            summary = row[2].strip() if len(row) > 2 else ""
            youtube_title = row[3].strip() if len(row) > 3 else ""
            # G列 (index 6) をステータスとして取得
            status = row[6].strip().lower() if len(row) > 6 else "pending"

            # 日付フィルタ
            if date_filter and date_val != date_filter:
                continue

            # pending または 空のステータスのみ処理
            if status not in ["pending", "", "未処理"]:
                continue

            # シナリオをパース
            dialogues = parse_scenario_text(scenario)

            if not dialogues:
                print(f"[SheetsReader] Warning: Row {idx} has no valid dialogues, skipping")
                continue

            pending_rows.append({
                "row_index": idx,
                "date": date_val,
                "scenario": scenario,
                "summary": summary,
                "youtube_title": youtube_title,
                "status": status,
                "dialogues": dialogues
            })

        print(f"[SheetsReader] Found {len(pending_rows)} pending row(s)")
        return pending_rows

    except HttpError as e:
        print(f"[SheetsReader] Google Sheets API error: {e}")
        raise
    except Exception as e:
        print(f"[SheetsReader] Error reading spreadsheet: {e}")
        raise


def update_row_status(
    row_index: int,
    status: str = "done",
    spreadsheet_id: Optional[str] = None
) -> bool:
    """
    スプレッドシートの特定行のステータスを更新

    Args:
        row_index: 行番号 (1-indexed)
        status: 新しいステータス値
        spreadsheet_id: スプレッドシートID

    Returns:
        成功した場合True
    """
    spreadsheet_id = spreadsheet_id or SHEETS_SPREADSHEET_ID

    if not spreadsheet_id:
        raise ValueError("SHEETS_SPREADSHEET_ID is not set")

    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()

        # SHEETS_RANGE からシート名を取得 (例: "シート1!A:G" -> "シート1")
        sheet_name = SHEETS_RANGE.split('!')[0] if '!' in SHEETS_RANGE else "シート1"
        
        # G列のステータスを更新
        range_name = f"{sheet_name}!G{row_index}"

        body = {
            'values': [[status]]
        }

        result = sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

        print(f"[SheetsReader] Updated row {row_index} status to '{status}'")
        return True

    except HttpError as e:
        print(f"[SheetsReader] Failed to update status: {e}")
        return False
    except Exception as e:
        print(f"[SheetsReader] Error updating status: {e}")
        return False


def get_today_scenarios() -> List[Dict[str, Any]]:
    """
    当日の処理待ちシナリオを取得

    Returns:
        当日のpending行リスト
    """
    today = datetime.now().strftime("%Y-%m-%d")
    return get_pending_rows(date_filter=today)


def get_all_pending_scenarios() -> List[Dict[str, Any]]:
    """
    全ての処理待ちシナリオを取得（日付に関係なく）

    Returns:
        全てのpending行リスト
    """
    return get_pending_rows(date_filter=None)


def create_script_from_sheet_row(row_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    スプレッドシートの行データを script.json 形式に変換

    Args:
        row_data: get_pending_rows() が返す行データ

    Returns:
        script.json 形式のデータ
        {
            "title": "...",
            "dialogues": [...],
            "summary": "...",
            "thumbnail_text": "..."
        }
    """
    return {
        "title": row_data.get("youtube_title", ""),
        "dialogues": row_data.get("dialogues", []),
        "summary": row_data.get("summary", ""),
        "thumbnail_text": row_data.get("youtube_title", "")[:20] if row_data.get("youtube_title") else "",
        "source": "spreadsheet",
        "sheet_row_index": row_data.get("row_index")
    }


def is_sheets_input_enabled() -> bool:
    """
    スプレッドシート入力が有効かどうか

    Returns:
        SHEETS_INPUT_ENABLED が true で、必要な設定がある場合 True
    """
    if not SHEETS_INPUT_ENABLED:
        return False

    if not SHEETS_SPREADSHEET_ID:
        print("[SheetsReader] Warning: SHEETS_INPUT_ENABLED is true but SHEETS_SPREADSHEET_ID is not set")
        return False

    if not GOOGLE_API_AVAILABLE:
        print("[SheetsReader] Warning: google-api-python-client is not available")
        return False

    return True


# テスト用
if __name__ == "__main__":
    print("=== Google Sheets Reader Test ===\n")

    # シナリオパースのテスト
    test_scenario = """A: こんにちは、今日は最新のAIニュースについてお話しします。
B: はい、よろしくお願いします！最近いろいろなニュースがありましたね。
A: そうですね。特に注目なのは、OpenAIの新しい発表です。
B: それは興味深いですね。詳しく教えてください。"""

    print("Test scenario parsing:")
    print(f"Input: {test_scenario[:50]}...")
    dialogues = parse_scenario_text(test_scenario)
    print(f"Parsed {len(dialogues)} dialogues:")
    for d in dialogues[:2]:
        print(f"  {d['speaker']}: {d['text'][:30]}...")
    print()

    # スプレッドシート読み込みテスト
    if is_sheets_input_enabled():
        print("Testing spreadsheet connection...")
        try:
            rows = get_pending_rows()
            print(f"Found {len(rows)} pending rows")
            for row in rows[:2]:
                print(f"  Row {row['row_index']}: {row['youtube_title'][:30]}...")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Spreadsheet input is not enabled.")
        print("Set SHEETS_INPUT_ENABLED=true and configure SHEETS_SPREADSHEET_ID")
        print(f"Current settings:")
        print(f"  SHEETS_INPUT_ENABLED: {SHEETS_INPUT_ENABLED}")
        print(f"  SHEETS_SPREADSHEET_ID: {SHEETS_SPREADSHEET_ID[:10]}..." if SHEETS_SPREADSHEET_ID else "  SHEETS_SPREADSHEET_ID: (not set)")
        print(f"  SHEETS_SERVICE_ACCOUNT_FILE: {SHEETS_SERVICE_ACCOUNT_FILE}")
