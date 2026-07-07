# Document Image Enhancement & Gemini OCR Pipeline

A modular, two-stage Python pipeline designed to preprocess document photos (e.g., handwritten drafts, receipts) using OpenCV and automatically transcribe them using the Gemini API. 

Both modules are fully decoupled and can be utilized completely independently depending on your project requirements.

---

## Features

### 1. Document Image Preprocessing (`cam_scanner.py`)
* **Standalone Operation:** Functions fully offline as a high-fidelity document enhancer without external API dependencies.
* **Perspective Correction:** Automatically detects document borders and performs pixel-level perspective warps to flatten skewed pages.
* **Adaptive Enhancement:** Wipes out harsh hand shadows, background noise, and paper discoloration using advanced thresholding and filtering.

### 2. Native Gemini OCR Engine (`raw_gemini_scanner.py`)
* **Standalone Operation:** Extracts text from any directory of pre-cleaned images or screenshots.
* **Zero SDK Dependency:** Built purely on the standard Python `requests` library to directly interact with Google's REST API, eliminating heavy package overhead.
* **Production-Ready Resilience:** Implements a strict 12-second post-success delay and an automatic 3-time retry mechanism to safely operate within Gemini Free-Tier QPS/RPM limits.

---

## Installation & Setup

Follow these steps to set up an isolated environment and install dependencies:

### 1. Navigate to the Project Directory
```bash
cd /path/to/your/project
```

### 2. Environment Isolation (Recommended)
Create and activate a virtual environment to prevent dependency conflicts:

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
Install the required lightweight packages via the requirements file:
```bash
pip install -r requirements.txt
```

> **Note:** Your `requirements.txt` file should contain the following dependencies:
> ```text
> opencv-python
> numpy
> requests
> python-dotenv
> ```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (same level as the scripts) and add your Gemini API key:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

---

## Folder Structure

The project dynamically maps inputs and outputs through the following directory layout:

```text
├── .env                  # Environment configuration file
├── requirements.txt      # Project dependencies
├── cam_scanner.py        # Stage 1: Document enhancer (Independent)
├── raw_gemini_scanner.py # Stage 2: REST API OCR script (Independent)
├── drafts/               # [Input for Stage 1] Place raw camera/smartphone photos here
└── scanned_output/       # [Output of Stage 1 / Input for Stage 2] Enhanced images
```

---

## Workflows

### Scenario A: Standalone Usage

#### 1. Image Enhancement Only (`cam_scanner.py`)
Use this module to crop, flatten, and clean documents without executing cloud OCR.
1. Drop raw photos (`.jpg`, `.png`, etc.) into the `./drafts/` directory (automatically created on first run if missing).
2. Run the enhancer:
   ```bash
   python cam_scanner.py
   ```
3. Find your polished, high-contrast images in the `./scanned_output/` folder prefixed with `scanned_`.

#### 2. Batch OCR Transcription Only (`raw_gemini_scanner.py`)
Use this module to transcribe text from pre-existing clean digital documents or screenshots.
1. Place target images directly into the `./scanned_output/` folder.
2. Verify that your `.env` file contains a valid `GEMINI_API_KEY`.
3. Run the script:
   ```bash
   python raw_gemini_scanner.py
   ```
4. Transcripts will compile chronologically into a timestamped file (e.g., `./ocr_2026-07-07_19-12.txt`) in the root directory.

### Scenario B: Full End-to-End Pipeline
To fully process a raw smartphone photo of handwritten text into a clean text document, execute the modules sequentially:
```bash
python cam_scanner.py
python raw_gemini_scanner.py
```

---

## Native API Reference

The OCR implementation bypasses the abstraction layers of official SDKs, sending standard HTTP `POST` requests directly to the Gemini REST API:

* **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}`
* **Payload Structure:**
```python
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
```