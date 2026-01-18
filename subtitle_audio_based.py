#!/usr/bin/env python3
"""
音声セグメントベースの正確な字幕生成モジュール

個別の音声ファイルの長さを直接計測し、累積時間から正確なSRT字幕を生成します。
これにより、音声と字幕の完璧な同期を実現します。

news-movie-generatorのsubtitle_generator_exact.pyを参考に実装
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional


def format_timestamp(milliseconds: int) -> str:
    """
    ミリ秒をSRT形式のタイムスタンプに変換

    Args:
        milliseconds: ミリ秒単位の時間

    Returns:
        SRT形式のタイムスタンプ (HH:MM:SS,mmm)
    """
    hours = milliseconds // 3600000
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    ms = milliseconds % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def parse_script_from_dialogues(dialogues: List[Dict]) -> List[Dict]:
    """
    ダイアログリストからセグメント情報を抽出

    Args:
        dialogues: [{"speaker": str, "text": str}, ...] の形式

    Returns:
        セグメント情報のリスト [{'speaker': str, 'text': str, 'index': int}, ...]
    """
    segments = []

    for i, dialogue in enumerate(dialogues):
        text = dialogue.get("text", "").strip()
        if not text:
            continue

        # マークダウンの太字を削除
        text = re.sub(r"\*\*", "", text)
        # 読点・句点の後ろのスペースを削除
        text = re.sub(r"[、,]\s*", "、", text)

        # 話者を正規化
        speaker = dialogue.get("speaker", "男性")
        if speaker in ["A", "Host A", "Main"]:
            speaker = "男性"
        elif speaker in ["B", "Host B", "Sub"]:
            speaker = "女性"

        segments.append({
            'speaker': speaker,
            'text': text,
            'index': i
        })

    return segments


def get_audio_duration(audio_path: str) -> int:
    """
    音声ファイルの長さをミリ秒単位で取得

    Args:
        audio_path: 音声ファイルのパス

    Returns:
        ミリ秒単位の長さ
    """
    # 方法1: pydubを使用
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_wav(audio_path)
        return len(audio)
    except Exception:
        pass

    # 方法2: ffprobeを使用（フォールバック）
    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        duration_sec = float(result.stdout.strip())
        return int(duration_sec * 1000)  # ミリ秒に変換
    except Exception as e:
        print(f"Error loading audio {audio_path}: {e}")
        return 0


def find_audio_files(audio_dir: str) -> List[Tuple[int, str]]:
    """
    音声ディレクトリから音声ファイルを検索し、インデックス順にソート

    Args:
        audio_dir: 音声ファイルがあるディレクトリ

    Returns:
        (インデックス, ファイルパス) のリスト
    """
    audio_files = []
    audio_path = Path(audio_dir)

    if not audio_path.exists():
        return []

    for wav_file in audio_path.glob("*.wav"):
        # ファイル名からインデックスを抽出 (chunk_0000.wav -> 0000)
        match = re.search(r"chunk_(\d+)\.wav$", wav_file.name)
        if match:
            index = int(match.group(1))
            audio_files.append((index, str(wav_file)))
        else:
            # ファイル名が異なる形式の場合、番号順にソート
            audio_files.append((len(audio_files), str(wav_file)))

    # インデックス順にソート
    audio_files.sort(key=lambda x: x[0])
    return audio_files


def split_text_for_subtitle(text: str, chars_per_line: int = 20, max_lines: int = 2) -> str:
    """
    字幕用にテキストを適切な長さに分割

    Args:
        text: 元のテキスト
        chars_per_line: 1行あたりの目標文字数
        max_lines: セグメントあたりの最大行数

    Returns:
        分割されたテキスト
    """
    # 自然な区切りでテキストを分割
    if len(text) <= chars_per_line * max_lines:
        return text

    # 句点で分割
    parts = []
    for part in re.split(r"[。！？]", text):
        if part.strip():
            parts.append(part.strip() + "。")

    # 長すぎる場合は読点でも分割
    if len(parts) <= 1 and len(text) > chars_per_line * 2:
        parts = []
        current_text = ""
        for char in text:
            current_text += char
            if char in "、," and len(current_text) >= chars_per_line:
                parts.append(current_text)
                current_text = ""
        if current_text:
            parts.append(current_text)

    subtitle_text = "\n".join(parts) if parts else text
    return subtitle_text


def generate_srt_from_audio_segments(
    dialogues: List[Dict],
    audio_dir: str,
    output_srt_path: str,
    chars_per_line: int = 20,
    max_lines: int = 2,
    inter_segment_pause_ms: int = 300
) -> bool:
    """
    音声セグメントの実際の長さに基づいてSRT字幕を生成

    Args:
        dialogues: ダイアログリスト [{"speaker": str, "text": str}, ...]
        audio_dir: 個別音声ファイルがあるディレクトリ
        output_srt_path: 出力SRTファイルのパス
        chars_per_line: 1行あたりの目標文字数
        max_lines: セグメントあたりの最大行数
        inter_segment_pause_ms: セグメント間のポーズ（ミリ秒）

    Returns:
        成功すればTrue
    """
    # スクリプトをパース
    segments = parse_script_from_dialogues(dialogues)

    if not segments:
        print("Warning: No valid segments found in dialogues")
        return False

    # 音声ファイルを検索
    audio_files = find_audio_files(audio_dir)

    if not audio_files:
        print(f"Warning: No audio files found in {audio_dir}")
        return False

    if len(segments) != len(audio_files):
        print(f"Warning: Script has {len(segments)} segments but found {len(audio_files)} audio files")
        print("Attempting to match available files...")

    # 出力ディレクトリを作成
    os.makedirs(os.path.dirname(output_srt_path) or ".", exist_ok=True)

    # SRTを生成
    with open(output_srt_path, "w", encoding="utf-8") as f:
        current_time = 0

        for i, (segment, (audio_idx, audio_path)) in enumerate(zip(segments, audio_files)):
            # 音声の長さを取得
            duration_ms = get_audio_duration(audio_path)

            if duration_ms == 0:
                print(f"Warning: Could not get duration for {audio_path}, skipping")
                continue

            # 開始・終了時間
            start_time = current_time
            end_time = current_time + duration_ms

            # テキストを適切な長さに分割
            text = segment['text']
            subtitle_text = split_text_for_subtitle(text, chars_per_line, max_lines)

            # SRT形式で書き込み
            f.write(f"{i + 1}\n")
            f.write(f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n")
            f.write(f"{subtitle_text}\n\n")

            # 次のセグメントの開始時間を更新（音声長 + セグメント間ポーズ）
            current_time = end_time + inter_segment_pause_ms

    print(f"✓ Generated: {output_srt_path}")
    print(f"  Segments: {len(audio_files)}")
    print(f"  Total duration: {current_time / 1000:.2f} seconds")
    print(f"  Inter-segment pause: {inter_segment_pause_ms}ms")

    return True


def generate_srt_from_combined_audio(
    dialogues: List[Dict],
    combined_audio_path: str,
    output_srt_path: str,
    estimated_timing: List[Dict] = None
) -> bool:
    """
    結合された音声ファイルとタイミングデータからSRT字幕を生成

    Args:
        dialogues: ダイアログリスト [{"speaker": str, "text": str}, ...]
        combined_audio_path: 結合された音声ファイルのパス
        output_srt_path: 出力SRTファイルのパス
        estimated_timing: タイミングデータ [{"start": float, "end": float, ...}, ...]

    Returns:
        成功すればTrue
    """
    if estimated_timing is None:
        print("Warning: No timing data provided, using fallback estimation")
        return False

    # 出力ディレクトリを作成
    os.makedirs(os.path.dirname(output_srt_path) or ".", exist_ok=True)

    # SRTを生成
    with open(output_srt_path, "w", encoding="utf-8") as f:
        for i, timing in enumerate(estimated_timing):
            start_ms = int(timing.get("start", 0) * 1000)
            end_ms = int(timing.get("end", 0) * 1000)

            text = timing.get("text", "").strip()
            if not text:
                continue

            # テキストを適切な長さに分割
            subtitle_text = split_text_for_subtitle(text)

            # SRT形式で書き込み
            f.write(f"{i + 1}\n")
            f.write(f"{format_timestamp(start_ms)} --> {format_timestamp(end_ms)}\n")
            f.write(f"{subtitle_text}\n\n")

    total_duration = estimated_timing[-1].get("end", 0) if estimated_timing else 0
    print(f"✓ Generated: {output_srt_path}")
    print(f"  Segments: {len(estimated_timing)}")
    print(f"  Total duration: {total_duration:.2f} seconds")

    return True


def main():
    """コマンドラインからの実行用"""
    if len(sys.argv) < 3:
        print("Usage: python subtitle_audio_based.py <audio_dir> <output.srt> [--dialogues json_file]", file=sys.stderr)
        print("\nExamples:")
        print("  # Use default test dialogues")
        print("  python subtitle_audio_based.py outputs/2025-01-18/video_001/chunks outputs/2025-01-18/video_001/subtitle.srt", file=sys.stderr)
        print("  # Use dialogues from JSON file")
        print("  python subtitle_audio_based.py outputs/2025-01-18/video_001/chunks outputs/2025-01-18/video_001/subtitle.srt --dialogues dialogues.json", file=sys.stderr)
        sys.exit(1)

    audio_dir = sys.argv[1]
    output_srt_path = sys.argv[2]

    # 入力の検証
    if not Path(audio_dir).exists():
        print(f"Error: Audio directory not found: {audio_dir}", file=sys.stderr)
        sys.exit(1)

    # ダイアログの読み込み
    dialogues = None
    if "--dialogues" in sys.argv:
        dialogues_idx = sys.argv.index("--dialogues")
        if dialogues_idx + 1 < len(sys.argv):
            dialogues_file = sys.argv[dialogues_idx + 1]
            try:
                with open(dialogues_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    dialogues = data.get("dialogues", [])
                print(f"Loaded {len(dialogues)} dialogues from {dialogues_file}")
            except Exception as e:
                print(f"Error loading dialogues from {dialogues_file}: {e}", file=sys.stderr)
                sys.exit(1)

    # フォールバック: デフォルトのテストダイアログ
    if dialogues is None:
        dialogues = [
            {"speaker": "男性", "text": "こんにちは、本日のニュースをお届けします。"},
            {"speaker": "女性", "text": "AIの進化が加速していますね。"},
        ]
        print("Using default test dialogues")

    # 字幕を生成
    success = generate_srt_from_audio_segments(
        dialogues=dialogues,
        audio_dir=audio_dir,
        output_srt_path=output_srt_path
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
