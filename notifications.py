"""
Notification System - Slack notifications for monitoring
Based on the blog's Slack notification system
"""
import os
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_notification(
    message: str,
    title: str = "AI Video Bot",
    color: str = "good",
    fields: Optional[list] = None
) -> bool:
    """
    Send a notification to Slack

    Args:
        message: Main message text
        title: Message title
        color: Color bar (good/warning/danger or hex)
        fields: List of field dicts with {"title": "", "value": "", "short": True}

    Returns:
        True if successful
    """
    if not SLACK_WEBHOOK_URL:
        print(f"[Slack] {title}: {message}")
        return False

    try:
        attachment = {
            "color": color,
            "title": title,
            "text": message,
            "ts": int(datetime.now().timestamp())
        }

        if fields:
            attachment["fields"] = fields

        payload = {
            "attachments": [attachment]
        }

        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            print(f"[Slack] Notification sent: {title}")
            return True
        else:
            print(f"[Slack] Failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"[Slack] Error: {e}")
        return False


def notify_video_start(video_number: int, topic: str, duration_minutes: int):
    """Notify when video generation starts"""
    send_slack_notification(
        message=f"動画生成を開始します",
        title=f"🎬 Video #{video_number} - Start",
        color="#36a64f",
        fields=[
            {"title": "トピック", "value": topic, "short": False},
            {"title": "目標時間", "value": f"{duration_minutes}分", "short": True},
            {"title": "開始時刻", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "short": True}
        ]
    )


def notify_video_complete(
    video_number: int,
    topic: str,
    video_path: str,
    duration_seconds: float,
    metadata: Optional[Dict[str, Any]] = None
):
    """Notify when video generation completes"""
    duration_str = f"{int(duration_seconds // 60)}分{int(duration_seconds % 60)}秒"

    fields = [
        {"title": "タイトル", "value": topic, "short": False},
        {"title": "動画時間", "value": duration_str, "short": True},
        {"title": "出力先", "value": video_path, "short": True}
    ]

    if metadata:
        if "youtube_title" in metadata:
            fields.append({"title": "YouTube Title", "value": metadata["youtube_title"], "short": False})
        if "tags" in metadata:
            tags_str = ", ".join(metadata["tags"][:5])
            fields.append({"title": "Tags", "value": tags_str, "short": False})

    send_slack_notification(
        message=f"動画生成が完了しました！ ✨",
        title=f"✅ Video #{video_number} - Complete",
        color="good",
        fields=fields
    )


def notify_video_error(
    video_number: int,
    topic: str,
    error: str,
    step: str = "Unknown"
):
    """Notify when an error occurs"""
    send_slack_notification(
        message=f"動画生成中にエラーが発生しました",
        title=f"❌ Video #{video_number} - Error",
        color="danger",
        fields=[
            {"title": "トピック", "value": topic, "short": False},
            {"title": "エラー箇所", "value": step, "short": True},
            {"title": "エラー内容", "value": error[:500], "short": False}
        ]
    )


def notify_daily_summary(
    total_videos: int,
    successful: int,
    failed: int,
    total_duration_minutes: float,
    topics: list
):
    """Send daily summary notification"""
    success_rate = (successful / total_videos * 100) if total_videos > 0 else 0

    topics_str = "\n".join([f"• {topic}" for topic in topics[:5]])
    if len(topics) > 5:
        topics_str += f"\n... and {len(topics) - 5} more"

    send_slack_notification(
        message=f"本日の動画生成が完了しました",
        title=f"📊 Daily Summary - {datetime.now().strftime('%Y-%m-%d')}",
        color="#4A90E2",
        fields=[
            {"title": "生成本数", "value": f"{successful}/{total_videos}", "short": True},
            {"title": "成功率", "value": f"{success_rate:.1f}%", "short": True},
            {"title": "失敗", "value": f"{failed}本", "short": True},
            {"title": "合計時間", "value": f"{int(total_duration_minutes)}分", "short": True},
            {"title": "トピック", "value": topics_str, "short": False}
        ]
    )


def notify_milestone(message: str, details: Optional[Dict[str, Any]] = None):
    """Notify about milestones (subscribers, views, etc.)"""
    fields = []
    if details:
        for key, value in details.items():
            fields.append({"title": key, "value": str(value), "short": True})

    send_slack_notification(
        message=message,
        title="🎉 Milestone Achieved!",
        color="#FFD700",
        fields=fields
    )


class NotificationContext:
    """Context manager for video generation notifications"""

    def __init__(self, video_number: int, topic: str, duration_minutes: int):
        self.video_number = video_number
        self.topic = topic
        self.duration_minutes = duration_minutes
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        notify_video_start(self.video_number, self.topic, self.duration_minutes)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Success
            elapsed = (datetime.now() - self.start_time).total_seconds()
            print(f"Video generation took {elapsed:.1f} seconds")
        else:
            # Error
            error_msg = f"{exc_type.__name__}: {exc_val}"
            notify_video_error(self.video_number, self.topic, error_msg)


if __name__ == "__main__":
    # Test notifications
    print("Testing Slack notifications...")

    notify_video_start(1, "Test Topic", 10)

    notify_video_complete(
        1, "Test Topic", "/path/to/video.mp4", 600,
        metadata={"youtube_title": "Test Video", "tags": ["test", "demo"]}
    )

    notify_daily_summary(
        total_videos=4,
        successful=3,
        failed=1,
        total_duration_minutes=120,
        topics=["Topic 1", "Topic 2", "Topic 3"]
    )

    print("Notification test complete!")
