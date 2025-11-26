#!/usr/bin/env python3
"""
既存の動画をYouTubeにアップロードするスクリプト
"""
import json
from pathlib import Path
from youtube_uploader import upload_video_with_metadata

def upload_video(video_dir_path: str):
    """指定されたディレクトリの動画をYouTubeにアップロード"""

    video_dir = Path(video_dir_path)

    # ファイルの存在確認
    video_path = video_dir / 'video.mp4'
    thumbnail_path = video_dir / 'thumbnail.jpg'
    metadata_path = video_dir / 'metadata.json'
    comments_path = video_dir / 'comments.json'

    if not video_path.exists():
        print(f"❌ 動画ファイルが見つかりません: {video_path}")
        return False

    # メタデータの読み込み
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # コメントの読み込み
    comments = []
    if comments_path.exists():
        with open(comments_path, 'r', encoding='utf-8') as f:
            comments_data = json.load(f)
            comments = comments_data.get('comments', [])

    print("=" * 60)
    print("📺 YouTube動画アップロード")
    print("=" * 60)
    print(f"📁 ディレクトリ: {video_dir}")
    print(f"🎬 タイトル: {metadata.get('youtube_title', 'N/A')}")
    print(f"⏱️  長さ: {metadata.get('duration_formatted', 'N/A')}")
    print(f"🖼️  サムネイル: {'あり' if thumbnail_path.exists() else 'なし'}")
    print(f"💬 コメント数: {len(comments)}")
    print()

    # アップロード実行
    result = upload_video_with_metadata(
        video_path=str(video_path),
        metadata=metadata,
        thumbnail_path=str(thumbnail_path) if thumbnail_path.exists() else None,
        comments=comments[:5],  # 最大5件
        privacy_status='unlisted'  # 限定公開
    )

    if result:
        print()
        print("=" * 60)
        print("🎉 アップロード成功！")
        print("=" * 60)
        print(f"📺 動画URL: {result['video_url']}")
        print(f"🆔 動画ID: {result['video_id']}")
        print(f"🔒 公開設定: {result['privacy_status']}")
        print()
        print("✅ YouTubeで確認できます！")
        print()

        # manifest.jsonを更新
        manifest_path = video_dir / 'manifest.json'
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            manifest['youtube_upload'] = result

            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

            print(f"✅ manifest.json を更新しました")

        return True
    else:
        print()
        print("❌ アップロード失敗")
        print()
        return False

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 upload_existing_video.py <video_directory>")
        print()
        print("例:")
        print("  python3 upload_existing_video.py outputs/2025-11-26/video_001")
        sys.exit(1)

    video_dir = sys.argv[1]
    success = upload_video(video_dir)

    sys.exit(0 if success else 1)
