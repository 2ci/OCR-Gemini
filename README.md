# Document Image Enhancement & Gemini OCR Pipeline

This repository provides a modular, two-stage pipeline to preprocess handwritten drafts or document photos and automatically transcribe them using the Gemini API. Built with flexibility in mind, **both scripts are fully decoupled and can be used completely independently** depending on your specific workflow requirements.

---

## Modular Features

1. **Document Image Preprocessing (`cam_scanner.py`)**
   * **Standalone Capability:** Can be used alone purely as an advanced document scanner filter without touching any cloud APIs or requiring an internet connection.
   * **Adaptive Filters:** Wipes out harsh hand shadows, inconsistent ambient lights, and background paper yellowing/noise.
   * **Perspective Correction:** Automatically detects document borders, auto-flattens skewed pages, and performs pixel-level aspect ratio correction.

2. **Native Gemini OCR Engine (`raw_gemini_scanner.py`)**
   * **Standalone Capability:** Can be used alone to batch-process and transcribe any pre-existing folder of images (such as standard screenshots or digital documents) directly.
   * **Zero SDK Dependency:** Directly communicates with Google's native REST API endpoint via the standard Python `requests` library to prevent versioning and dependency conflicts.
   * **Rate-Limit & Retry Guard:** Equipped with a 12-second post-success delay and a 3-time automatic retry mechanism to strictly respect Gemini Free-Tier QPS/RPM limits.

---

## Installation & Setup

Follow these steps to set up an isolated virtual environment and install the necessary project dependencies:

### 1. Clone or Navigate to the Project Directory
Open your terminal and enter the project root folder:
```bash
cd /path/to/your/project