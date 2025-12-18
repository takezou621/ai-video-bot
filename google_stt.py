"""
Google Speech-to-Text API integration for accurate subtitle timing
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import subprocess


def transcribe_audio_with_timing(audio_path: str, dialogues: List[Dict]) -> Optional[List[Dict]]:
    """
    Use Google Speech-to-Text to extract accurate timing from generated audio

    Args:
        audio_path: Path to audio file (MP3)
        dialogues: List of dialogue segments with speaker and text

    Returns:
        List of timing data with start/end times, or None if failed
    """
    try:
        # Convert MP3 to WAV for better compatibility
        wav_path = Path(audio_path).with_suffix('.wav')
        subprocess.run([
            'ffmpeg', '-y', '-i', audio_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',  # 16kHz for speech recognition
            '-ac', '1',      # Mono
            str(wav_path)
        ], check=True, capture_output=True)

        # Use Gemini API for speech recognition (if available)
        try:
            import google.generativeai as genai
            import os

            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("  GEMINI_API_KEY not found, using fallback")
                wav_path.unlink()
                return None

            genai.configure(api_key=api_key)

            # Upload audio file
            audio_file = genai.upload_file(str(wav_path))

            # Request transcription with timing
            model = genai.GenerativeModel('gemini-3-flash-preview')

            prompt = """この音声を書き起こし、各発話の正確な開始時刻と終了時刻を秒単位で提供してください。

JSON形式で以下のように出力してください：
```json
[
  {
    "speaker": "A",
    "text": "発話内容",
    "start": 0.0,
    "end": 3.5
  }
]
```

音声を注意深く聞いて、実際の発話タイミングに基づいて時刻を記録してください。"""

            response = model.generate_content([audio_file, prompt])

            # Parse JSON response
            response_text = response.text
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text.strip()

            timing_data = json.loads(json_str)

            # Clean up
            wav_path.unlink()

            print(f"  ✅ Google STT: Extracted timing for {len(timing_data)} segments")
            return timing_data

        except Exception as e:
            print(f"  ⚠️  Gemini transcription failed: {e}")
            wav_path.unlink()
            return None

    except Exception as e:
        print(f"  ❌ Audio conversion failed: {e}")
        return None


def analyze_audio_energy(audio_path: str, dialogues: List[Dict]) -> List[Dict]:
    """
    Analyze audio energy levels to detect speech segments

    This is a fallback method when API-based transcription is not available.
    """
    try:
        import numpy as np
        import subprocess

        # Extract audio samples using ffmpeg
        result = subprocess.run([
            'ffmpeg', '-i', audio_path,
            '-f', 's16le',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            'pipe:1'
        ], capture_output=True, check=True)

        # Parse audio data
        audio_data = np.frombuffer(result.stdout, dtype=np.int16)
        sample_rate = 16000

        # Calculate energy in windows
        window_size = int(sample_rate * 0.1)  # 100ms windows
        hop_size = int(sample_rate * 0.05)     # 50ms hop

        energies = []
        for i in range(0, len(audio_data) - window_size, hop_size):
            window = audio_data[i:i+window_size]
            energy = np.sqrt(np.mean(window.astype(float)**2))
            energies.append(energy)

        # Detect speech segments
        threshold = np.mean(energies) * 0.3
        is_speech = np.array(energies) > threshold

        # Find segment boundaries
        segments = []
        in_speech = False
        start_idx = 0

        for i, speaking in enumerate(is_speech):
            if speaking and not in_speech:
                start_idx = i
                in_speech = True
            elif not speaking and in_speech:
                end_idx = i
                start_time = start_idx * hop_size / sample_rate
                end_time = end_idx * hop_size / sample_rate
                segments.append((start_time, end_time))
                in_speech = False

        # Map segments to dialogues
        timing_data = []
        for i, dialogue in enumerate(dialogues):
            if i < len(segments):
                start, end = segments[i]
            else:
                # Fallback to estimation
                if timing_data:
                    start = timing_data[-1]['end'] + 0.2
                else:
                    start = 0
                end = start + max(2.0, len(dialogue['text']) / 7.0)

            timing_data.append({
                'speaker': dialogue['speaker'],
                'text': dialogue['text'],
                'start': start,
                'end': end
            })

        print(f"  ✅ Energy-based timing: {len(timing_data)} segments detected")
        return timing_data

    except Exception as e:
        print(f"  ❌ Energy analysis failed: {e}")
        return None


if __name__ == '__main__':
    # Test with existing audio
    audio_path = 'outputs/2025-11-26/video_001/dialogue.mp3'

    with open('outputs/2025-11-26/video_001/script.json', 'r', encoding='utf-8') as f:
        script = json.load(f)
        dialogues = script['dialogues']

    print("Testing Google Speech-to-Text timing extraction...")
    timing_data = transcribe_audio_with_timing(audio_path, dialogues)

    if timing_data:
        print("\nTiming data:")
        for i, t in enumerate(timing_data[:3]):
            print(f"  {i+1}. [{t['start']:.1f}s - {t['end']:.1f}s] {t['speaker']}: {t['text'][:30]}...")
    else:
        print("\nFalling back to energy analysis...")
        timing_data = analyze_audio_energy(audio_path, dialogues)
        if timing_data:
            print("\nTiming data:")
            for i, t in enumerate(timing_data[:3]):
                print(f"  {i+1}. [{t['start']:.1f}s - {t['end']:.1f}s] {t['speaker']}: {t['text'][:30]}...")
