import os
import torch
from pathlib import Path

# Try to import TTS, but don't fail immediately
try:
    from TTS.api import TTS
    HAS_COQUI = True
except ImportError:
    HAS_COQUI = False

# Configuration from environment
COQUI_MODEL_NAME = os.getenv("COQUI_MODEL_NAME", "tts_models/multilingual/multi-dataset/xtts_v2")
COQUI_USE_GPU = os.getenv("COQUI_USE_GPU", "true").lower() == "true"
DEVICE = "cuda" if torch.cuda.is_available() and COQUI_USE_GPU else "cpu"

# Monkey patch torch.load to handle PyTorch 2.6+ security changes
# Coqui TTS uses older pickle protocols that are now restricted by default
original_load = torch.load
def safe_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return original_load(*args, **kwargs)
torch.load = safe_load

# Singleton model instance
_tts_model = None

def _get_model():
    """Lazy load the TTS model."""
    global _tts_model
    if _tts_model is None:
        if not HAS_COQUI:
            raise ImportError("Coqui TTS ('TTS' package) is not installed.")
        
        print(f"[INFO] Initializing Coqui TTS with model: {COQUI_MODEL_NAME} on {DEVICE}")
        
        # Agree to terms for models like XTTS
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        try:
            # Force CPU if GPU issues arise, or use DEVICE from env
            _tts_model = TTS(COQUI_MODEL_NAME).to(DEVICE)
        except Exception as e:
            print(f"[ERROR] Failed to load Coqui TTS model: {e}")
            raise
            
    return _tts_model

def generate_voice(text: str, output_path: Path, speaker: str = "male") -> Path:
    """
    Generate speech audio using Coqui TTS.
    """
    model = _get_model()
    
    kwargs = {}
    
    # Assume XTTS v2 setup for now as it's the default
    # Skip complex attribute checks that are causing issues
    
    speaker_wav = None
    if speaker == "female":
        speaker_wav = os.getenv("COQUI_FEMALE_SPEAKER_WAV")
    else:
        speaker_wav = os.getenv("COQUI_MALE_SPEAKER_WAV")
        
    if not speaker_wav or not os.path.exists(speaker_wav):
        # Fallback to default assets if env vars not set or file missing
        default_wav = Path("assets/voices/male.wav")
        if default_wav.exists():
            speaker_wav = str(default_wav)
            
    if speaker_wav:
        kwargs["speaker_wav"] = speaker_wav
    
    # Handle multilingual models
    if "multilingual" in COQUI_MODEL_NAME.lower() or "xtts" in COQUI_MODEL_NAME.lower():
        kwargs["language"] = "ja"

    print(f"Generating TTS with args: {kwargs}")
    
    # Generate the file
    model.tts_to_file(text=text, file_path=str(output_path), **kwargs)
    
    return output_path

def is_available() -> bool:
    """Check if Coqui TTS is installed and properly configured."""
    return HAS_COQUI
