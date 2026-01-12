# Fix Summary

I have scanned the project and fixed the following critical errors:

1.  **`app.py` (Mode Selection Logic):**
    *   **Issue:** The operating mode was hardcoded to `'2'` (Lightweight), ignoring user input and command-line arguments.
    *   **Fix:** Restored the ability to select mode interactively or via arguments (`--light`, `--default`). Added a fallback to 'Light' mode if no input is provided (safe default).

2.  **`main.py` (Error Handling):**
    *   **Issue:** The main execution block used `try...except: pass`, which silently swallowed all errors, making debugging impossible.
    *   **Fix:** Changed to print critical errors and stack traces using `traceback`, so you can see why the application fails if it does.

3.  **Diagnostic Check (`diagnose_ai.py`):**
    *   **Status:** Ran a diagnostic scan.
    *   **Result:** The system is code-complete but requires an API Key to function fully.
    *   **Action Required:** Please add your `GOOGLE_API_KEY` or `GEMINI_API_KEY` to the `.env` file.

## Next Steps
1.  Add your API key to `.env`.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run the app: `python app.py`
