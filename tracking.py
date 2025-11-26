"""
Video Tracking System - Google Sheets logging
Based on the blog's Google Sheets tracking approach
"""
import os
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Google Sheets API (simplified - using a webhook/API endpoint)
SHEETS_WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL")
SHEETS_API_KEY = os.getenv("GOOGLE_SHEETS_API_KEY")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Alternative: Use local JSON file for tracking
TRACKING_FILE = Path(__file__).parent / "outputs" / "video_log.json"


def log_video_to_sheets(
    video_data: Dict[str, Any]
) -> bool:
    """
    Log video data to Google Sheets

    Args:
        video_data: Dictionary with video information

    Returns:
        True if successful
    """
    # Ensure tracking file exists
    TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Always log locally
    _log_locally(video_data)

    # Try to log to Google Sheets if configured
    if SHEETS_WEBHOOK_URL:
        return _log_to_google_sheets_webhook(video_data)
    elif SHEETS_API_KEY and SPREADSHEET_ID:
        return _log_to_google_sheets_api(video_data)
    else:
        print("[Tracking] No Google Sheets configured, using local log only")
        return True


def _log_locally(video_data: Dict[str, Any]):
    """Log video data to local JSON file"""
    try:
        # Load existing log
        if TRACKING_FILE.exists():
            with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                log = json.load(f)
        else:
            log = {"videos": []}

        # Add new entry
        log["videos"].append(video_data)

        # Save
        with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

        print(f"[Tracking] Logged locally: {video_data.get('title', 'Unknown')}")
        return True

    except Exception as e:
        print(f"[Tracking] Local log error: {e}")
        return False


def _log_to_google_sheets_webhook(video_data: Dict[str, Any]) -> bool:
    """Log to Google Sheets via webhook (e.g., Zapier, Make.com)"""
    try:
        response = requests.post(
            SHEETS_WEBHOOK_URL,
            json=video_data,
            timeout=10
        )

        if response.status_code == 200:
            print(f"[Tracking] Logged to Sheets: {video_data.get('title', 'Unknown')}")
            return True
        else:
            print(f"[Tracking] Sheets webhook failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"[Tracking] Sheets webhook error: {e}")
        return False


def _log_to_google_sheets_api(video_data: Dict[str, Any]) -> bool:
    """Log to Google Sheets via Google Sheets API"""
    try:
        # Format data as row
        row = [
            video_data.get("timestamp", ""),
            video_data.get("video_id", ""),
            video_data.get("title", ""),
            video_data.get("duration_seconds", 0),
            video_data.get("category", ""),
            ", ".join(video_data.get("tags", [])),
            video_data.get("status", "generated"),
            video_data.get("file_path", ""),
        ]

        # Append to sheet
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Videos!A:H:append"
        params = {
            "valueInputOption": "RAW",
            "key": SHEETS_API_KEY
        }
        payload = {
            "values": [row]
        }

        response = requests.post(url, params=params, json=payload, timeout=10)

        if response.status_code == 200:
            print(f"[Tracking] Logged to Google Sheets: {video_data.get('title', 'Unknown')}")
            return True
        else:
            print(f"[Tracking] Google Sheets API failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"[Tracking] Google Sheets API error: {e}")
        return False


def create_video_log_entry(
    video_id: str,
    title: str,
    file_path: str,
    duration_seconds: float,
    metadata: Optional[Dict[str, Any]] = None,
    topic_data: Optional[Dict[str, Any]] = None,
    status: str = "generated"
) -> Dict[str, Any]:
    """
    Create a standardized video log entry

    Args:
        video_id: Unique video ID (e.g., date-based)
        title: Video title
        file_path: Path to video file
        duration_seconds: Video duration
        metadata: Video metadata (tags, description, etc.)
        topic_data: Original topic data
        status: Video status (generated, uploaded, published, failed)

    Returns:
        Formatted log entry
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "video_id": video_id,
        "title": title,
        "file_path": str(file_path),
        "duration_seconds": duration_seconds,
        "duration_display": f"{int(duration_seconds // 60)}:{int(duration_seconds % 60):02d}",
        "status": status,
    }

    if metadata:
        entry["youtube_title"] = metadata.get("youtube_title", "")
        entry["youtube_description"] = metadata.get("youtube_description", "")
        entry["tags"] = metadata.get("tags", [])
        entry["category"] = metadata.get("category", "Education")
        entry["hashtags"] = metadata.get("hashtags", [])

    if topic_data:
        entry["topic"] = topic_data.get("title", "")
        entry["topic_angle"] = topic_data.get("angle", "")
        entry["topic_source"] = topic_data.get("selected_topic", {}).get("source", "")

    return entry


def get_video_statistics() -> Dict[str, Any]:
    """Get statistics from video log"""
    try:
        if not TRACKING_FILE.exists():
            return {"total_videos": 0, "total_duration_minutes": 0}

        with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
            log = json.load(f)

        videos = log.get("videos", [])

        total_duration = sum(v.get("duration_seconds", 0) for v in videos)
        successful = sum(1 for v in videos if v.get("status") == "generated")
        failed = sum(1 for v in videos if v.get("status") == "failed")

        # Group by date
        by_date = {}
        for v in videos:
            date = v.get("timestamp", "")[:10]  # Get date part
            by_date[date] = by_date.get(date, 0) + 1

        return {
            "total_videos": len(videos),
            "successful": successful,
            "failed": failed,
            "total_duration_minutes": total_duration / 60,
            "total_duration_hours": total_duration / 3600,
            "videos_by_date": by_date,
            "latest_video": videos[-1] if videos else None
        }

    except Exception as e:
        print(f"[Tracking] Statistics error: {e}")
        return {"total_videos": 0, "error": str(e)}


def export_tracking_to_csv(output_path: Optional[Path] = None) -> Path:
    """Export tracking data to CSV"""
    import csv

    if output_path is None:
        output_path = TRACKING_FILE.parent / "video_log.csv"

    try:
        if not TRACKING_FILE.exists():
            print("[Tracking] No data to export")
            return None

        with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
            log = json.load(f)

        videos = log.get("videos", [])

        if not videos:
            print("[Tracking] No videos to export")
            return None

        # Write CSV
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            # Get all unique keys
            all_keys = set()
            for v in videos:
                all_keys.update(v.keys())

            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()

            for v in videos:
                # Flatten lists to strings
                row = {}
                for k, val in v.items():
                    if isinstance(val, (list, dict)):
                        row[k] = json.dumps(val, ensure_ascii=False)
                    else:
                        row[k] = val
                writer.writerow(row)

        print(f"[Tracking] Exported to CSV: {output_path}")
        return output_path

    except Exception as e:
        print(f"[Tracking] CSV export error: {e}")
        return None


if __name__ == "__main__":
    # Test tracking
    test_data = create_video_log_entry(
        video_id="2025-11-26-001",
        title="Test Video",
        file_path="/path/to/video.mp4",
        duration_seconds=600,
        metadata={
            "youtube_title": "Test Video Title",
            "tags": ["test", "demo"],
            "category": "Education"
        },
        status="generated"
    )

    log_video_to_sheets(test_data)

    stats = get_video_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    export_tracking_to_csv()
