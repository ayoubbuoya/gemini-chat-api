from flask import Flask, jsonify, request
import os
import sqlite3
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import uuid

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
            chat_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# --- API Endpoints ---


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'user_id' not in data or 'message' not in data:
        return jsonify({'error': 'Missing user_id or message'}), 400

    user_id = data['user_id']
    message = data['message']
    chat_id = data.get('chat_id')  # Optional chat_id (for existing chats)

    if not chat_id:  # Create new chat ID if it doesn't exist
        chat_id = str(uuid.uuid4())

    # Load chat history for specific chat
    chat_history = get_chat_history(user_id, chat_id)

    # Start or get the chat object
    chat = get_or_create_chat_session(user_id, chat_id, chat_history)

    # Send message to Gemini and store response
    gemini_response = send_message_to_gemini(chat, message)
    store_message(user_id, chat_id, "user", message)
    store_message(user_id, chat_id, "model", gemini_response)

    # return chat_id as well to let user be aware
    return jsonify({'response': gemini_response, 'chat_id': chat_id})


@app.route('/history/<user_id>', methods=['GET'])
def get_user_chat_sessions(user_id):
    sessions = get_all_chat_ids(user_id)
    return jsonify({'chat_sessions': sessions})


@app.route('/history/<user_id>/<chat_id>', methods=['GET'])
def get_chat_history_api(user_id, chat_id):
    history = get_chat_history(user_id, chat_id)
    return jsonify({'history': [dict(row) for row in history]})

# --- Helper Functions ---


def get_chat_history(user_id, chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM chat_history WHERE user_id = ? AND chat_id = ? ORDER BY timestamp", (user_id, chat_id))
    history = cursor.fetchall()
    conn.close()
    return history


def get_all_chat_ids(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT chat_id FROM chat_history WHERE user_id = ?", (user_id,))
    sessions = [row["chat_id"] for row in cursor.fetchall()]
    conn.close()
    return sessions


# A mapping to hold chat objects so that users can continue their conversations.
chat_sessions = {}


def get_or_create_chat_session(user_id, chat_id, chat_history):
    key = (user_id, chat_id)  # Using tuples as dict keys
    if key in chat_sessions:
        chat = chat_sessions[key]
        return chat
    else:
        chat = model.start_chat(history=[{"role": row["role"], "parts": [
                                row["content"]]} for row in chat_history])
        chat_sessions[key] = chat
        return chat


def send_message_to_gemini(chat, user_message):
    try:
        response = chat.send_message(user_message)
        return response.text
    except Exception as e:
        return f"Error with Gemini: {str(e)}"


def store_message(user_id, chat_id, role, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (user_id, chat_id, role, content) VALUES (?, ?, ?, ?)",
                   (user_id, chat_id, role, content))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()  # Initialize database on startup
    app.run(debug=True)
