import os
import base64
import time
from datetime import datetime
import requests
from dotenv import load_dotenv  # Import load_dotenv to read the .env file

# ================= Configuration Area =================
# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INPUT_FOLDER = "./scanned_output"

# Dynamically generate filename based on current time (Format: ocr_YYYY-MM-DD_HH-MM.txt)
current_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
OUTPUT_TXT = f"./ocr_{current_time_str}.txt"
# ======================================================

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def scan_with_raw_api(img_path):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    img_base64 = image_to_base64(img_path)
    
    strict_prompt = (
        "You are a strict, professional OCR scanner specializing in handwritten text. "
        "Your ONLY task is to transcribe the handwritten text from the image exactly as it is written. "
        "Rules: 1. Do not fix grammar or spelling. 2. Do not rephrase. 3. Output ONLY raw text."
    )
    
    payload = {
        "contents": [{
            "parts": [
                {"text": strict_prompt},
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": img_base64
                    }
                }
            ]
        }]
    }
    
    response = requests.post(url, json=payload, timeout=60)
    
    if response.status_code == 200:
        result = response.json()
        try:
            return result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            raise Exception(f"Abnormal API response structure. Recognition might have failed. Full response: {result}")
    else:
        raise Exception(f"API Error (Status Code {response.status_code}): {response.text}")

def main():
    print("==================================================")
    print("🚀 Gemini Native API Batch OCR Scanner Started")
    print("==================================================")

    # 1. Automatically check and create input folder
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"⚠️ Folder '{INPUT_FOLDER}' does not exist, created automatically.")
        print(f"💡 Please place your images into this directory, then rerun the script.")
        return

    # 2. Filter and get image list
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    image_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(valid_extensions)]
    
    if not image_files:
        print(f"❌ No image files found in '{INPUT_FOLDER}' folder.")
        print(f"👉 Please ensure image extensions are jpg/jpeg/png and placed inside the folder.")
        return

    total_files = len(image_files)
    print(f"📂 Directory loaded successfully, found {total_files} images pending for scan.")
    print(f"📝 OCR results will be saved in real-time to: {OUTPUT_TXT}\n")
    print("--------------------------------------------------")

    # 3. Start loop processing and print real-time logs
    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f_out:
        for idx, img_name in enumerate(image_files, 1):
            img_path = os.path.join(INPUT_FOLDER, img_name)
            
            # Terminal real-time log: Start scanning
            print(f"⏳ [{idx}/{total_files}] Processing: {img_name} ...", end="", flush=True)
            f_out.write(f"=== Filename: {img_name} ===\n\n")
            
            start_time = time.time()
            
            # Core logic: Retry loop
            max_retries = 3  # Retry up to 3 times
            text_result = None
            success = False
            
            try:
                for attempt in range(max_retries + 1):
                    try:
                        text_result = scan_with_raw_api(img_path)
                        success = True
                        break  # Request successful, break the retry loop
                    except Exception as e:
                        if attempt < max_retries:
                            # Terminal warning: Retrying after error or rate limit
                            print(f"\r⚠️ [{idx}/{total_files}] Request restricted or error occurred. Performing retry #{attempt + 1}...", end="", flush=True)
                            time.sleep(4)
                        else:
                            # Throw exception to outer block if all retries fail
                            raise e
                
                # Write successful result to file
                f_out.write(text_result)
                f_out.write("\n\n" + "="*40 + "\n\n")
                
                elapsed = time.time() - start_time
                print(f"\r✅ [{idx}/{total_files}] Success! Time elapsed: {elapsed:.2f} seconds.")
                
                # Enforce a 12-second interval after each successful conversion to prevent QPS/RPM limits
                time.sleep(12)
                
            except Exception as e:
                # All 4 attempts (1 regular + 3 retries) failed
                print(f"\r❌ [{idx}/{total_files}] Processing failed after 3 retries.")
                print(f"   Final error cause: {e}")
                f_out.write(f"[This file failed to scan. Error still persists after retries: {e}]\n\n========================================\n\n")
                
                # Give the API a 5-second cooldown period even if it fails
                time.sleep(5)

    print("\n==================================================")
    print(f"🎉 All scanning tasks completed! Recognized text saved in: {OUTPUT_TXT}")
    print("==================================================")

if __name__ == "__main__":
    main()