from flask import Flask, jsonify, request
import os
import sqlite3
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- Database Setup ---
DATABASE = 'chat_history.db'
# Gemini Model to use
MODEL_NAME = "models/gemini-2.0-flash-exp"


# --- Gemini API Setup ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


print("Google Api Key", GOOGLE_API_KEY)

genai.configure(api_key=GOOGLE_API_KEY)


model = genai.GenerativeModel(MODEL_NAME)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# --- API Endpoints - --


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'user_id' not in data or 'message' not in data:
        return jsonify({'error': 'Missing user_id or message'}), 400

    user_id = data['user_id']
    user_message = data['message']

    # Load chat history from the database
    chat_history = get_chat_history(user_id)

    # Send message to Gemini 1.5 Pro with context
    gemini_response = send_to_gemini(chat_history, user_message)

    # Store user and model response in the database
    store_message(user_id, "user", user_message)
    store_message(user_id, "model", gemini_response)

    return jsonify({'response': gemini_response})


@app.route('/history/<user_id>', methods=['GET'])
def get_chat_history_api(user_id):
    history = get_chat_history(user_id)
    # Convert rows to dictionaries
    return jsonify({'history': [dict(row) for row in history]})

# --- Helper Functions ---


def get_chat_history(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY timestamp", (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history


def send_to_gemini(chat_history, user_message):
    messages = []
    for row in chat_history:
        messages.append({"role": row["role"], "parts": [row["content"]]})
    messages.append({"role": "user", "parts": [user_message]})

    try:
        response = model.generate_content(messages)
        return response.text
    except Exception as e:
        return f"Error with Gemini: {str(e)}"


def store_message(user_id, role, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
    conn.commit()
    conn.close()


@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "Pong!"}), 200


if __name__ == '__main__':
    init_db()  # Initialize database on startup
    app.run(debug=True)
