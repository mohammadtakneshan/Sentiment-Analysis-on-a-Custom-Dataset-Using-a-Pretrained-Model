import os
from flask import Flask, request, jsonify, render_template
from transformers import pipeline
import torch

app = Flask(__name__)

# Detect device (GPU or CPU)
device = 0 if torch.cuda.is_available() else -1

# Load a single multilingual sentiment analysis model
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    device=device
)

# Mapping star ratings to human-readable sentiment labels
def map_sentiment_label(label):
    if label in ["1 star", "2 stars"]:
        return "Negative"
    elif label == "3 stars":
        return "Neutral"
    elif label in ["4 stars", "5 stars"]:
        return "Positive"
    else:
        return "Unknown"

@app.route('/')
def home():
    return render_template('app.html')  # Ensure app.html is in the 'templates' folder

@app.route('/analyze', methods=['POST'])
def analyze_sentiment():
    data = request.json
    texts = data.get('texts', [])

    if not texts:
        return jsonify({"error": "No texts provided"}), 400

    if not isinstance(texts, list) or any(not isinstance(text, str) for text in texts):
        return jsonify({"error": "Invalid input format. Expected a list of strings."}), 400

    try:
        # Batch processing for better performance
        analyses = sentiment_analyzer(texts)
        results = [
            {
                "text": text,
                "label": map_sentiment_label(analysis['label'])
            }
            for text, analysis in zip(texts, analyses)
        ]
    except Exception as e:
        # Log the error and return a general error response
        app.logger.error(f"Error analyzing sentiment: {e}")
        return jsonify({"error": "An error occurred during analysis"}), 500

    return jsonify(results)

if __name__ == '__main__':
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode)