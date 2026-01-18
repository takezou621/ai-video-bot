#!/usr/bin/env python3
"""
シンプルな動画生成モジュール (FFmpegベース)

background.pngを背景に使用し、音声と字幕SRTを組み合わせてMP4動画を生成します。
news-movie-generatorのvideo_generator.pyを参考に実装。
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def get_ffmpeg_path() -> Optional[str]:
    """
    FFmpegのパスを取得

    Returns:
        FFmpegのパス、見つからない場合はNone
    """
    # 優先順位付きでffmpegを検索
    paths_to_try = [
        "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",  # Homebrew ffmpeg-full
        "/opt/homebrew/bin/ffmpeg",  # Homebrew ffmpeg
        "/usr/local/bin/ffmpeg",  # Common location
    ]

    for path in paths_to_try:
        if Path(path).exists():
            return path

    # shutil.whichでシステムのffmpegを検索
    return shutil.which("ffmpeg")


def check_ffmpeg() -> bool:
    """
    FFmpegがインストールされているか確認

    Returns:
        FFmpegが利用可能ならTrue
    """
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        return False

    try:
        subprocess.run(
            [ffmpeg_path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def generate_mp4_with_subtitle(
    audio_path: str,
    subtitle_path: str,
    output_mp4_path: str,
    background_image_path: Optional[str] = None,
    background_color: str = "black",
    resolution: str = "1920x1080"
) -> bool:
    """
    音声と字幕からMP4動画を生成

    Args:
        audio_path: 音声ファイルパス（wav, mp3等）
        subtitle_path: 字幕SRTファイルパス
        output_mp4_path: 出力MP4ファイルパス
        background_image_path: 背景画像パス（オプション、指定がない場合は背景色を使用）
        background_color: 背景色（デフォルト: black）
        resolution: 動画解像度（デフォルト: 1920x1080）

    Returns:
        成功すればTrue、失敗すればFalse
    """
    # 入力ファイルの存在確認
    if not Path(audio_path).exists():
        print(f"Error: Audio file not found: {audio_path}")
        return False

    if not Path(subtitle_path).exists():
        print(f"Error: Subtitle file not found: {subtitle_path}")
        return False

    # 背景画像の指定がある場合は存在確認
    use_bg_image = False
    bg_abs = None
    if background_image_path:
        bg_path = Path(background_image_path)
        if bg_path.exists():
            use_bg_image = True
            bg_abs = str(bg_path.resolve())
            print(f"Using background image: {background_image_path}")
        else:
            print(f"Warning: Background image not found: {background_image_path}")
            print(f"Using background color instead: {background_color}")

    # FFmpegの確認
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path or not check_ffmpeg():
        print("Error: FFmpeg is not installed or not in PATH")
        print("Install FFmpeg:")
        print("  macOS:   brew install ffmpeg")
        print("  Ubuntu:  sudo apt-get install ffmpeg")
        print("  Windows: https://ffmpeg.org/download.html")
        return False

    # 出力ディレクトリを作成
    output_abs = str(Path(output_mp4_path).resolve())
    os.makedirs(Path(output_mp4_path).parent, exist_ok=True)

    # 字幕ファイルのエスケープ処理
    def escape_subtitle_path(path: str) -> str:
        """FFmpeg subtitlesフィルター用のパスエスケープ"""
        # 最初にバックスラッシュをエスケープ（コロンエスケープより先に行う）
        escaped = path.replace("\\", "\\\\")
        # 次にコロンをエスケープ（Windows用）
        escaped = escaped.replace(":", "\\:")
        # FFmpegのsubtitlesフィルター用にfilename=を追加
        return f"filename={escaped}"

    audio_abs = str(Path(audio_path).resolve())

    if use_bg_image:
        # 背景画像を使用する場合
        # 字幕ファイルが存在するか確認
        subtitle_valid = Path(subtitle_path).exists()

        if subtitle_valid:
            # 字幕付き
            subtitle_escaped = escape_subtitle_path(subtitle_path)
            cmd_list = [
                ffmpeg_path,
                "-y",
                "-loop", "1",
                "-i", bg_abs,
                "-i", audio_abs,
                "-vf", f"subtitles={subtitle_escaped}",
                "-shortest",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                output_abs
            ]
        else:
            # 字幕なし
            print("Warning: Subtitle file not found, generating video without subtitles")
            cmd_list = [
                ffmpeg_path,
                "-y",
                "-loop", "1",
                "-i", bg_abs,
                "-i", audio_abs,
                "-shortest",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                output_abs
            ]
    else:
        # 背景色を使用する場合
        subtitle_escaped = escape_subtitle_path(subtitle_path)
        cmd_list = [
            ffmpeg_path,
            "-y",
            "-f", "lavfi",
            "-i", f"color=c={background_color}:s={resolution}:d=3600",
            "-i", audio_abs,
            "-vf", f"subtitles={subtitle_escaped}",
            "-shortest",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            output_abs
        ]

    print(f"\nGenerating MP4: {output_mp4_path}")
    print(f"  Audio: {audio_path}")
    print(f"  Subtitle: {subtitle_path}")
    print(f"  Resolution: {resolution}")

    try:
        # FFmpegを実行
        result = subprocess.run(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print(f"FFmpeg error:")
            print(result.stderr)
            return False

        # ファイルが生成されたか確認
        if Path(output_abs).exists():
            print(f"✓ Generated: {output_abs}")
            return True
        else:
            print("Error: Output file was not created")
            return False

    except Exception as e:
        print(f"Error generating MP4: {e}")
        return False


def main():
    """コマンドラインからの実行用"""
    if len(sys.argv) < 4:
        print("Usage: python video_generator_simple.py <audio_file> <subtitle_srt> <output_mp4>", file=sys.stderr)
        print("\nExample:")
        print("  python video_generator_simple.py audio.wav subtitle.srt output.mp4", file=sys.stderr)
        print("\nOptions:")
        print("  --bg <path>   Background image (default: background.png in current dir)")
        sys.exit(1)

    audio_path = sys.argv[1]
    subtitle_path = sys.argv[2]
    output_mp4_path = sys.argv[3]

    # オプション: 背景画像
    bg_path = None
    if "--bg" in sys.argv:
        bg_idx = sys.argv.index("--bg")
        if bg_idx + 1 < len(sys.argv):
            bg_path = sys.argv[bg_idx + 1]
    else:
        # デフォルトのbackground.pngを探す
        default_bg = Path.cwd() / "background.png"
        if default_bg.exists():
            bg_path = str(default_bg)

    # 動画を生成
    success = generate_mp4_with_subtitle(
        audio_path=audio_path,
        subtitle_path=subtitle_path,
        output_mp4_path=output_mp4_path,
        background_image_path=bg_path
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
