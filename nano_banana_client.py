import os, base64, requests, time
from pathlib import Path
from PIL import Image, ImageDraw

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def _dummy(prompt, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB",(1792,1024),(40,80,120))
    d = ImageDraw.Draw(img)
    d.text((20,20),"DUMMY IMAGE",(255,255,255))
    img.save(out_path)
    return out_path

def generate_image(prompt, out_path:Path, max_retries=3):
    if not OPENAI_API_KEY:
        return _dummy(prompt, out_path)

    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "dall-e-3",
        "prompt": f"Cinematic 16:9 landscape image, film photography style: {prompt}",
        "n": 1,
        "size": "1792x1024",
        "response_format": "b64_json"
    }

    for attempt in range(max_retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            data = r.json()
            if "error" in data:
                error_msg = data["error"].get("message", "Unknown API error")
                if "rate_limit" in error_msg.lower():
                    wait_time = 65  # Wait 65 seconds for rate limit reset
                    print(f"Rate limit hit, waiting {wait_time}s... (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                print("API Error:", data["error"])
                raise Exception(error_msg)
            img_b64 = data["data"][0]["b64_json"]
            img_bytes = base64.b64decode(img_b64)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            open(out_path, "wb").write(img_bytes)
            return out_path
        except Exception as e:
            if attempt < max_retries - 1 and "rate_limit" in str(e).lower():
                continue
            print("fallback:", e)
            return _dummy(prompt, out_path)

    return _dummy(prompt, out_path)
