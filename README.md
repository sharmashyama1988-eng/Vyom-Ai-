# Vyom AI

Vyom AI is an advanced, multi-modal AI assistant designed to provide accurate, well-structured responses, content generation, and system integration. It features a Flask-based web interface and a standalone visualizer.

## Features

*   **Multi-Engine Support**: Uses Google Gemini (Flash/Pro) as the core brain, with fallbacks to web search.
*   **Modes**:
    *   **Light Mode**: Uses Cloud APIs (Gemini) for reasoning. Low resource usage.
    *   **Default Mode**: Intended for local LLMs (requires GPU/RAM), currently falls back to Cloud/Light mode if hardware is insufficient.
*   **Voice Interaction**: Supports voice input and output (System TTS or ElevenLabs).
*   **Visual Studio**: Basic image editing and generation capabilities.
*   **Web Interface**: Clean, chat-based UI.

## Prerequisites

*   Python 3.10 or higher.
*   A Google Gemini API Key (Get one from [Google AI Studio](https://aistudio.google.com/)).
*   (Optional) FFmpeg for advanced audio/video processing.

## Installation

1.  **Clone the repository** (if you haven't already).
2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Create a file named `.env` in the root directory.
2.  Add your API keys. You can use `.env.example` as a template.

**Example `.env` content:**
```ini
# Google Gemini API Key (Required)
GOOGLE_API_KEY=your_actual_api_key_here

# Or multiple keys for rotation (comma separated)
GOOGLE_API_KEYS=key1,key2,key3

# ElevenLabs API Key (Optional, for realistic voice)
ELEVENLABS_API_KEY=your_elevenlabs_key
```

## Usage

### Web Interface (Recommended)
Run the web server:
```bash
python app.py
```
*   Select "Lightweight Mode" (Option 2) if asked.
*   Open your browser and navigate to `http://localhost:5000`.

### Visualizer (Experimental)
Run the standalone agent visualizer:
```bash
python main.py
```

## Troubleshooting

*   **Missing Dependencies**: If you see errors about missing modules, run `pip install -r requirements.txt` again.
*   **API Errors**: Ensure your `GOOGLE_API_KEY` is valid and has quota.
*   **Audio Issues**: If TTS fails, it might default to system voice. Ensure audio drivers are working.
