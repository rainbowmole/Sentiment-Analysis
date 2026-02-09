import traceback
import logging
from flask import Flask, render_template, request, jsonify
from vader_sentiment import SentimentAnalyzer
from flask_cors import CORS
import webbrowser

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)                     # allow cross-origin for local testing
analyzer = SentimentAnalyzer()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    app.logger.debug("Received /analyze POST")   # <-- helps confirm request arrived
    data = request.get_json() or {}
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "empty text"}), 400
    try:
        res = analyzer.analyze(text)
        return jsonify(res)
    except Exception as e:
        tb = traceback.format_exc()
        app.logger.exception("Error during analysis")
        # For local debugging only — do not expose stack traces in production
        return jsonify({"error": str(e), "traceback": tb}), 500

if __name__ == "__main__":
    url = "http://127.0.0.1:8000"
    webbrowser.open_new_tab(url)
    app.run(host="127.0.0.1", port=8000, debug=True)