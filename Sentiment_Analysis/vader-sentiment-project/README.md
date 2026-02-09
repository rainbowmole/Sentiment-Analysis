# Vader Sentiment Project

Quick guide — which file to run / open and known problem file.

Modes
- Server mode (Flask + VADER — recommended for full Python analyzer)
  - Run the Flask app:
    ```powershell
    # from project root
    python vader-sentiment-project\src\web_app.py
    ```
  - Open in browser:
    ```
    http://127.0.0.1:8000
    ```
  - Files used:
    - Server entry: vader-sentiment-project\src\web_app.py
    - Template served by Flask: vader-sentiment-project\src\templates\index.html

  - Test API from PowerShell:
    ```powershell
    Invoke-RestMethod -Uri 'http://127.0.0.1:8000/analyze' -Method Post -ContentType 'application/json' -Body (@{ text = 'I love matcha' } | ConvertTo-Json)
    ```
  - Or use real curl (avoid PowerShell alias):
    ```powershell
    curl.exe -v -X POST -H "Content-Type: application/json" -d '{"text":"I love matcha"}' http://127.0.0.1:8000/analyze
    ```

- Static / client-only mode (no Python required)
  - Open directly in a browser (double-click) or serve statically:
    ```
    vader-sentiment-project\src\templates\index_static.html
    ```
  - To serve with a simple HTTP server:
    ```powershell
    python -m http.server 8000
    # then open:
    http://127.0.0.1:8000/vader-sentiment-project/src/templates/index_static.html
    ```

- Terminal / CLI mode (app.py)
  - Use app.py when you want to run the analyzer from a terminal (no web UI).
  - Run interactively or show help:
    ```powershell
    # interactive / default behavior
    python vader-sentiment-project\src\app.py

    # show CLI options (if available)
    python vader-sentiment-project\src\app.py -h
    ```
  - Expected behavior:
    - Running app.py will start a simple command-line interface to analyze text (enter text at the prompt or pass options shown by `-h`).
    - If app.py depends on the same analyzer/NLTK resources, ensure you installed requirements and NLTK data first:
      ```powershell
      pip install -r vader-sentiment-project\requirements.txt
      python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
      ```
  - If you prefer piping text:
    ```powershell
    # if app.py supports reading stdin or a text arg (check -h)
    echo "I love matcha" | python vader-sentiment-project\src\app.py
    ```

Known problem (what caused "Failed to fetch")
- Do NOT open `vader-sentiment-project\src\templates\index.html` using file:// in the browser.
  - index.html expects the Flask backend at `/analyze`. Loading it from the filesystem makes the browser fail to POST (shows "Failed to fetch").
  - Fix: either (A) run the Flask server and open http://127.0.0.1:8000, or (B) use `index_static.html` for a serverless demo, or (C) use `app.py` for terminal usage.

Troubleshooting
- If you see "Failed to fetch" in the browser:
  - Confirm you loaded the page from `http://127.0.0.1:8000` (server mode) or opened `index_static.html` directly (static mode).
  - Check Flask terminal for GET / and POST /analyze logs.
  - If using PowerShell, avoid the built-in `curl` alias — use `curl.exe` or `Invoke-RestMethod`.

Files
- Flask app: vader-sentiment-project\src\web_app.py
- Server UI template: vader-sentiment-project\src\templates\index.html
- Static demo (no server): vader-sentiment-project\src\templates\index_static.html
- CLI/terminal interface: vader-sentiment-project\src\app.py
- Analyzer: vader-sentiment-