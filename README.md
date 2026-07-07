# Document Image Enhancement & Gemini OCR Pipeline

This project provides a robust, two-stage pipeline to preprocess handwritten drafts or document photos and automatically transcribe them using the Gemini API. It features high-fidelity image enhancement via OpenCV and a pure `requests`-based API interaction layer to completely avoid heavy SDK dependencies.

---

## Features

1. **Advanced Image Preprocessing (`cam_filter.py` / `cam_scanner.py`)**
   * **Standalone Capability:** Can be used independently to crop, rotate, flatten, and contrast-enhance any document or handwritten draft photo.
   * **Adaptive Filters:** Removes hand shadows, ambient dim lights, and background paper yellowing/noise.
   * **Perspective Correction:** Automatically detects document edges and performs pixel-level flattening.

2. **Native Gemini OCR Engine (`raw_gemini_scanner.py`)**
   * **Zero SDK Dependency:** Uses the standard Python `requests` library to directly interact with Google's native REST API endpoint.
   * **Rate-Limit Guard:** Enforces a strict 12-second cooldown interval between successful requests to prevent hitting Free-Tier RPM/QPS limitations.
   * **Robust Error Handling:** Embedded with a 3-time retry mechanism to safely recover from unexpected network hiccups or `429 Too Many Requests` status codes.

---

## Installation & Setup

### 1. Install Dependencies
Ensure you have Python installed, then run the following command to install the required lightweight libraries:
```bash
pip install opencv-python numpy requests python-dotenv