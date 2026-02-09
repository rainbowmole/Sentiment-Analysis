@echo off
REM Start Flask server in a new window (assumes python on PATH)
start "" cmd /k "python vader-sentiment-project\src\web_app.py"
exit