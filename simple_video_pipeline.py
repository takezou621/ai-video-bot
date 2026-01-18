#!/usr/bin/env python3
"""
シンプル動画生成パイプライン

シナリオからbackground.pngを背景にした字幕付きMP4動画を生成します。
news-movie-generatorのアプローチを採用：
1. シナリオをパース
2. 音声生成（VOICEVOX/Gemini TTS）
3. 音声セグメントから正確な字幕タイミングを生成
4. FFmpegで背景画像＋音声＋字幕を組み合わせて動画生成

このリポジトリ内で完結する実装（news-movie-generatorへの参照なし）
"""
import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib

# プロジェクト内のモジュールをインポート
import tts_generator
import subtitle_audio_based
import video_generator_simple


def parse_script_file(script_path: str) -> List[Dict]:
    """
    スクリプトファイルをパースしてダイアログリストを取得

    Args:
        script_path: スクリプトファイルのパス
                    Host A: テキスト または Host B: テキスト 形式

    Returns:
        ダイアログリスト [{"speaker": "男性"/"女性", "text": "..."}, ...]
    """
    dialogues = []

    with open(script_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Host A/Host B 形式をパース
            if line.startswith("Host A:") or line.startswith("Host B:"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    host = parts[0].strip()
                    text = parts[1].strip()

                    # Host A -> 男性, Host B -> 女性
                    speaker = "男性" if host == "Host A" else "女性"
                    dialogues.append({"speaker": speaker, "text": text})
            # 男性/女性 形式をパース
            elif line.startswith("男性:") or line.startswith("女性:"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    text = parts[1].strip()
                    dialogues.append({"speaker": speaker, "text": text})
            # 男性（田中太郎）のような形式
            elif "男性" in line[:10] and "：" in line:
                parts = line.split("：", 1)
                if len(parts) == 2:
                    text = parts[1].strip()
                    dialogues.append({"speaker": "男性", "text": text})
            elif "女性" in line[:10] and "：" in line:
                parts = line.split("：", 1)
                if len(parts) == 2:
                    text = parts[1].strip()
                    dialogues.append({"speaker": "女性", "text": text})

    return dialogues


def parse_scenario_json(scenario_path: str) -> List[Dict]:
    """
    シナリオJSONファイルをパースしてダイアログリストを取得

    Args:
        scenario_path: シナリオJSONファイルのパス
                       {"dialogues": [{"speaker": "男性"/"女性", "text": "..."}]} 形式

    Returns:
        ダイアログリスト
    """
    with open(scenario_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get("dialogues", [])


def generate_video_from_script(
    script_path: str,
    output_dir: str,
    background_image: Optional[str] = None
) -> bool:
    """
    スクリプトファイルから動画を生成

    Args:
        script_path: スクリプトファイルのパス
        output_dir: 出力ディレクトリ
        background_image: 背景画像のパス（Noneの場合はプロジェクトルートのbackground.png）

    Returns:
        成功すればTrue
    """
    print("=" * 60)
    print("シンプル動画生成パイプライン")
    print("=" * 60)

    # 出力ディレクトリを作成
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # スクリプトをパース
    print(f"\n[Step 1] スクリプトを読み込み: {script_path}")
    dialogues = parse_script_file(script_path)

    if not dialogues:
        print(f"Error: No dialogues found in {script_path}")
        return False

    print(f"  Found {len(dialogues)} dialogues")

    # 背景画像のパスを決定
    if background_image is None:
        # プロジェクトルートのbackground.pngを使用
        project_root = Path(__file__).parent
        default_bg = project_root / "background.png"
        background_image = str(default_bg) if default_bg.exists() else None

    if background_image and Path(background_image).exists():
        print(f"  Background: {background_image}")
    else:
        print("  Warning: No background image found, using black background")

    # 音声生成
    print(f"\n[Step 2] 音声を生成")
    audio_path = output_path / "dialogue.mp3"

    try:
        audio_result, timing_data = tts_generator.generate_dialogue_audio(
            dialogues=dialogues,
            output_path=audio_path
        )
        print(f"  ✓ Audio generated: {audio_result}")
        print(f"  Timing entries: {len(timing_data)}")
    except Exception as e:
        print(f"  ✗ Audio generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 字幕生成
    print(f"\n[Step 3] 字幕を生成")

    # チャンクディレクトリを確認
    chunks_dir = output_path / "chunks"

    if chunks_dir.exists():
        # 音声セグメントから正確なタイミングで字幕生成
        subtitle_path = output_path / "subtitle.srt"
        success = subtitle_audio_based.generate_srt_from_audio_segments(
            dialogues=dialogues,
            audio_dir=str(chunks_dir),
            output_srt_path=str(subtitle_path)
        )
        if success:
            print(f"  ✓ Subtitle generated from audio segments")
        else:
            # フォールバック: タイミングデータから字幕生成
            subtitle_path = output_path / "subtitle.srt"
            success = subtitle_audio_based.generate_srt_from_combined_audio(
                dialogues=dialogues,
                combined_audio_path=str(audio_result),
                output_srt_path=str(subtitle_path),
                estimated_timing=timing_data
            )
            if success:
                print(f"  ✓ Subtitle generated from timing data")
            else:
                print(f"  ✗ Subtitle generation failed")
                return False
    else:
        # タイミングデータから字幕生成
        subtitle_path = output_path / "subtitle.srt"
        success = subtitle_audio_based.generate_srt_from_combined_audio(
            dialogues=dialogues,
            combined_audio_path=str(audio_result),
            output_srt_path=str(subtitle_path),
            estimated_timing=timing_data
        )
        if not success:
            print(f"  ✗ Subtitle generation failed")
            return False

    # 動画生成
    print(f"\n[Step 4] 動画を生成")
    video_path = output_path / "video.mp4"

    success = video_generator_simple.generate_mp4_with_subtitle(
        audio_path=str(audio_result),
        subtitle_path=str(subtitle_path),
        output_mp4_path=str(video_path),
        background_image_path=background_image
    )

    if success:
        print(f"\n✓ 動画生成完了!")
        print(f"  Output: {video_path}")
        return True
    else:
        print(f"\n✗ 動画生成に失敗しました")
        return False


def generate_video_from_scenario_json(
    scenario_path: str,
    output_dir: str,
    background_image: Optional[str] = None
) -> bool:
    """
    シナリオJSONファイルから動画を生成

    Args:
        scenario_path: シナリオJSONファイルのパス
        output_dir: 出力ディレクトリ
        background_image: 背景画像のパス

    Returns:
        成功すればTrue
    """
    print("=" * 60)
    print("シンプル動画生成パイプライン (JSON入力)")
    print("=" * 60)

    # 出力ディレクトリを作成
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # シナリオをパース
    print(f"\n[Step 1] シナリオJSONを読み込み: {scenario_path}")
    dialogues = parse_scenario_json(scenario_path)

    if not dialogues:
        print(f"Error: No dialogues found in {scenario_path}")
        return False

    print(f"  Found {len(dialogues)} dialogues")

    # 背景画像のパスを決定
    if background_image is None:
        project_root = Path(__file__).parent
        default_bg = project_root / "background.png"
        background_image = str(default_bg) if default_bg.exists() else None

    if background_image and Path(background_image).exists():
        print(f"  Background: {background_image}")

    # 音声生成
    print(f"\n[Step 2] 音声を生成")
    audio_path = output_path / "dialogue.mp3"

    try:
        audio_result, timing_data = tts_generator.generate_dialogue_audio(
            dialogues=dialogues,
            output_path=audio_path
        )
        print(f"  ✓ Audio generated: {audio_result}")
    except Exception as e:
        print(f"  ✗ Audio generation failed: {e}")
        return False

    # 字幕生成
    print(f"\n[Step 3] 字幕を生成")
    subtitle_path = output_path / "subtitle.srt"

    # チャンクディレクトリを確認
    chunks_dir = output_path / "chunks"

    if chunks_dir.exists():
        success = subtitle_audio_based.generate_srt_from_audio_segments(
            dialogues=dialogues,
            audio_dir=str(chunks_dir),
            output_srt_path=str(subtitle_path)
        )
    else:
        success = subtitle_audio_based.generate_srt_from_combined_audio(
            dialogues=dialogues,
            combined_audio_path=str(audio_result),
            output_srt_path=str(subtitle_path),
            estimated_timing=timing_data
        )

    if not success:
        print(f"  ✗ Subtitle generation failed")
        return False

    # 動画生成
    print(f"\n[Step 4] 動画を生成")
    video_path = output_path / "video.mp4"

    success = video_generator_simple.generate_mp4_with_subtitle(
        audio_path=str(audio_result),
        subtitle_path=str(subtitle_path),
        output_mp4_path=str(video_path),
        background_image_path=background_image
    )

    if success:
        print(f"\n✓ 動画生成完了!")
        print(f"  Output: {video_path}")
        return True
    else:
        return False


def generate_video_from_dialogues(
    dialogues: List[Dict],
    output_dir: str,
    background_image: Optional[str] = None
) -> Tuple[bool, Path]:
    """
    ダイアログリストから直接動画を生成

    Args:
        dialogues: ダイアログリスト [{"speaker": "男性"/"女性", "text": "..."}]
        output_dir: 出力ディレクトリ
        background_image: 背景画像のパス

    Returns:
        (成功したかどうか, 動画ファイルのパス)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 背景画像のパスを決定
    if background_image is None:
        project_root = Path(__file__).parent
        default_bg = project_root / "background.png"
        background_image = str(default_bg) if default_bg.exists() else None

    print(f"[Simple Pipeline] Generating video from {len(dialogues)} dialogues...")

    # 音声生成
    audio_path = output_path / "dialogue.mp3"
    try:
        audio_result, timing_data = tts_generator.generate_dialogue_audio(
            dialogues=dialogues,
            output_path=audio_path
        )
    except Exception as e:
        print(f"[Simple Pipeline] Audio generation failed: {e}")
        return False, Path()

    # 字幕生成
    subtitle_path = output_path / "subtitle.srt"
    chunks_dir = output_path / "chunks"

    if chunks_dir.exists():
        success = subtitle_audio_based.generate_srt_from_audio_segments(
            dialogues=dialogues,
            audio_dir=str(chunks_dir),
            output_srt_path=str(subtitle_path)
        )
    else:
        success = subtitle_audio_based.generate_srt_from_combined_audio(
            dialogues=dialogues,
            combined_audio_path=str(audio_result),
            output_srt_path=str(subtitle_path),
            estimated_timing=timing_data
        )

    if not success:
        return False, Path()

    # 動画生成
    video_path = output_path / "video.mp4"
    success = video_generator_simple.generate_mp4_with_subtitle(
        audio_path=str(audio_result),
        subtitle_path=str(subtitle_path),
        output_mp4_path=str(video_path),
        background_image_path=background_image
    )

    return success, video_path


def main():
    """コマンドラインからの実行"""
    import argparse

    parser = argparse.ArgumentParser(
        description="シンプル動画生成パイプライン - シナリオから字幕付きMP4動画を生成"
    )
    parser.add_argument(
        "input",
        help="スクリプトファイルまたはシナリオJSONファイルのパス"
    )
    parser.add_argument(
        "-o", "--output",
        default="output/simple_video",
        help="出力ディレクトリ (デフォルト: output/simple_video)"
    )
    parser.add_argument(
        "--bg",
        help="背景画像のパス (デフォルト: プロジェクトルートのbackground.png)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # 入力ファイル形式の判定
    if input_path.suffix == ".json":
        success = generate_video_from_scenario_json(
            scenario_path=str(input_path),
            output_dir=args.output,
            background_image=args.bg
        )
    else:
        success = generate_video_from_script(
            script_path=str(input_path),
            output_dir=args.output,
            background_image=args.bg
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
