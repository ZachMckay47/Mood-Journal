from flask import Flask, request, jsonify, send_file
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import sqlite3
import os

app = Flask(__name__)
analyzer = SentimentIntensityAnalyzer()

# Initialize SQLite database
DB_FILE = "mood_journal.db"

def init_db():
    """Initialize the SQLite database and create the table if it doesn't exist."""
    if not os.path.exists(DB_FILE):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS moods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    transcript TEXT,
                    mood TEXT
                )
            """)
            conn.commit()

@app.route('/webhook', methods=['POST'])
@app.route('/webhook/', methods=['POST'])
def handle_transcript():
    """Handle incoming transcripts and perform mood analysis."""
    data = request.json
    transcript = data.get('text', '')

    # Perform sentiment analysis
    mood_analysis = analyze_emotion(transcript)

    # Save to database
    save_to_db(transcript, mood_analysis)

    # Log data to console
    print(f"Transcript: {transcript} | Mood: {mood_analysis}")

    return jsonify({"status": "success", "mood_analysis": mood_analysis})

@app.route('/moods', methods=['GET'])
def get_moods():
    """Retrieve all moods stored in the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM moods ORDER BY timestamp DESC")
        rows = cursor.fetchall()
    results = [{"id": row[0], "timestamp": row[1], "transcript": row[2], "mood": row[3]} for row in rows]
    return jsonify(results)

@app.route('/setup', methods=['GET'])
def setup_page():
    """Serve the setup.html file."""
    return send_file("setup.html")

def analyze_emotion(transcript):
    """Analyze the sentiment of a transcript and classify mood."""
    if not transcript.strip():
        return "Neutral"
    sentiment = analyzer.polarity_scores(transcript)
    if sentiment['compound'] >= 0.6:
        return "Very Positive"
    elif sentiment['compound'] >= 0.2:
        return "Positive"
    elif sentiment['compound'] <= -0.6:
        return "Very Negative"
    elif sentiment['compound'] <= -0.2:
        return "Negative"
    else:
        return "Neutral"

def save_to_db(transcript, mood):
    """Save a transcript and its mood analysis to the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO moods (transcript, mood) VALUES (?, ?)", (transcript, mood))
        conn.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
