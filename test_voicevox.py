import os
import voicevox_client
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Override for local testing outside Docker if needed
if not os.getenv("VOICEVOX_URL"):
    os.environ["VOICEVOX_URL"] = "http://localhost:50021"

def test_voicevox():
    print("Testing VOICEVOX Integration...")
    
    if not voicevox_client.is_available():
        print(f"❌ VOICEVOX engine is not reachable at {os.environ['VOICEVOX_URL']}")
        return

    text = "こんにちは。ボイスボックスによるローカル音声合成のテストです。ずんだもんがお送りします。"
    output_dir = Path("outputs/tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test Male (Zundamon by default)
    output_path = output_dir / "voicevox_test_male.wav"
    print(f"Generating male voice...")
    result = voicevox_client.generate_voice(text, output_path, speaker_type="male")
    if result and result.exists():
        print(f"✅ Success! Male voice saved to: {output_path}")
        
    # Test Female (Metan by default)
    output_path_female = output_dir / "voicevox_test_female.wav"
    print(f"Generating female voice...")
    result_f = voicevox_client.generate_voice(text, output_path_female, speaker_type="female")
    if result_f and result_f.exists():
        print(f"✅ Success! Female voice saved to: {output_path_female}")

if __name__ == "__main__":
    test_voicevox()
