import os
import json
import requests
from pathlib import Path
from typing import Optional

# Configuration
VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://voicevox:50021")
# Default Speaker IDs (can be configured via .env)
# 3: ずんだもん (Standard), 2: 四国めたん (Standard)
SPEAKER_MALE = int(os.getenv("VOICEVOX_MALE_ID", "3"))
SPEAKER_FEMALE = int(os.getenv("VOICEVOX_FEMALE_ID", "2"))

def is_available() -> bool:
    """Check if VOICEVOX engine is reachable."""
    try:
        response = requests.get(f"{VOICEVOX_URL}/speakers", timeout=3)
        return response.status_code == 200
    except Exception:
        return False

def generate_voice(text: str, output_path: Path, speaker_type: str = "male") -> Optional[Path]:
    """
    Generate speech using VOICEVOX engine.
    
    Args:
        text: Text to synthesize.
        output_path: Path to save the wav file.
        speaker_type: 'male' or 'female'.
        
    Returns:
        Path to the generated file or None if failed.
    """
    speaker_id = SPEAKER_FEMALE if speaker_type == "female" else SPEAKER_MALE
    
    try:
        # 1. Create Audio Query
        params = {
            "text": text,
            "speaker": speaker_id
        }
        query_response = requests.post(
            f"{VOICEVOX_URL}/audio_query",
            params=params,
            timeout=30
        )
        if query_response.status_code != 200:
            print(f"[VOICEVOX] Error in audio_query: {query_response.text}")
            return None
            
        query_data = query_response.json()
        
        # Optional: Adjust speed or pitch here if needed
        # query_data["speedScale"] = 1.1
        
        # 2. Synthesis
        synthesis_response = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": speaker_id},
            json=query_data,
            timeout=60
        )
        
        if synthesis_response.status_code != 200:
            print(f"[VOICEVOX] Error in synthesis: {synthesis_response.text}")
            return None
            
        # 3. Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(synthesis_response.content)
            
        print(f"[VOICEVOX] Voice generated at {output_path} (Speaker: {speaker_id})")
        return output_path
        
    except Exception as e:
        print(f"[VOICEVOX] Connection failed: {e}")
        return None
