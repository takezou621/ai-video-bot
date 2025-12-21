import os
from pathlib import Path
from dotenv import load_dotenv
import coqui_tts

# Load environment variables
load_dotenv()

# Force CPU for testing to avoid 5070 Ti compatibility issues with older PyTorch
os.environ["COQUI_USE_GPU"] = "false"

def test_coqui():
    print("Testing Coqui TTS Integration...")
    
    if not coqui_tts.is_available():
        print("❌ Coqui TTS is not installed (TTS package missing).")
        return

    # Mock dialogue
    text = "こんにちは。これはローカルのコーキー・ティー・ティー・エスによる音声合成のテストです。"
    output_dir = Path("outputs/tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "coqui_test_male.wav"
    
    print(f"Generating voice for: '{text}'")
    try:
        # Test male voice
        coqui_tts.generate_voice(text, output_path, speaker="male")
        if output_path.exists():
            print(f"✅ Success! Male voice saved to: {output_path}")
        
        # Test female voice
        output_path_female = output_dir / "coqui_test_female.wav"
        coqui_tts.generate_voice(text, output_path_female, speaker="female")
        if output_path_female.exists():
            print(f"✅ Success! Female voice saved to: {output_path_female}")
            
    except Exception as e:
        print(f"❌ Failed to generate voice: {e}")

if __name__ == "__main__":
    test_coqui()
