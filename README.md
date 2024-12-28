# Gemini Chat API

This project provides a RESTful API for interacting with the Google Gemini model. It allows users to send messages and maintain chat history. The API uses Flask, SQLite, and the Google Gemini API.

## Features

- **User Management:** Creates and manages user data in a database.
- **Chat Session Management:** Creates and stores chat sessions for each user.
- **Message Handling:** Sends messages to the Gemini model and stores them in the database.
- **Chat History:** Retrieves chat history for specific users and chat sessions.
- **Persistent Storage:** Uses SQLite to store user data, chat sessions, and chat history.
- **Session Persistence:** Maintains chat sessions in memory for a smooth conversational experience.

## Technologies Used

- **Python:** The core programming language.
- **Flask:** A micro web framework for creating the API.
- **SQLite:** A lightweight database for storing chat history.
- **Google Gemini API:** For interacting with the Gemini model.
- **python-dotenv:** For managing environment variables.

## Setup

## Running the Application

1.  **Initialize the database:**

    The database initialization happens automatically when the application runs. If the database file does not exist, it will create it.

2.  **Run the application:**

    ```bash
    python app.py
    ```

    The API will be available at `http://127.0.0.1:5000`.

## API Endpoints

### POST /chat

Sends a message to the Gemini model and stores the conversation.

**Request Body:**

```json
{
  "user_id": "unique_user_id",
  "message": "Hello, Gemini!",
  "chat_id": "optional_chat_id"
}
```

- `user_id` (required): The unique identifier for the user.
- `message` (required): The message to send to the Gemini model.
- `chat_id` (optional): The existing chat id which can be retrieved through `/history/<user_id>` API.

**Response:**

```json
{
  "response": "Hi there! How can I assist you?",
  "chat_id": "unique_chat_id"
}
```

- `response`: The response from Gemini.
- `chat_id`: The chat id created or used in the request.

### GET /history/\<user_id\>

Retrieves all chat sessions for a given user.

**Parameters:**

- `user_id`: The unique identifier for the user.

**Response:**

```json
{
  "chat_sessions": ["chat_id_1", "chat_id_2"]
}
```

### GET /history/\<user_id\>/\<chat_id\>

Retrieves the chat history for a specific chat session.

**Parameters:**

- `user_id`: The unique identifier for the user.
- `chat_id`: The identifier for the chat session.

**Response:**

```json
{
  "history": [
    {
      "role": "user",
      "content": "Hi, Gemini"
    },
    {
      "role": "model",
      "content": "Hello, User!"
    }
  ]
}
```

## Database Schema

The SQLite database has the following tables:

- **users**: Stores user information.
  - `user_id` (TEXT, PRIMARY KEY): Unique user identifier.
  - `username` (TEXT): User's username.
  - `email` (TEXT): User's email.
- **chat_sessions**: Stores chat session information.
  - `chat_id` (TEXT, PRIMARY KEY): Unique chat session identifier.
  - `user_id` (TEXT, NOT NULL, FOREIGN KEY): User identifier associated with the session.
  - `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP): Creation timestamp of the session.
- **chat_history**: Stores individual messages in a chat session.
  - `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT): Unique message identifier.
  - `chat_id` (TEXT, NOT NULL, FOREIGN KEY): Chat session identifier.
  - `timestamp` (DATETIME, DEFAULT CURRENT_TIMESTAMP): Timestamp of the message.
  - `role` (TEXT, NOT NULL): The role of the message sender (user or model).
  - `content` (TEXT, NOT NULL): The message content.

## Important Notes

- Ensure you have a valid Google API key set in the `.env` file.
- The application saves a chat session in memory so that the conversation is continued without losing context.
- The database file `chat_history.db` is created in the same directory as the application script.

## Contributing

Feel free to fork the repository and submit pull requests with improvements or bug fixes.
