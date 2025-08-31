---
license: apache-2.0
title: sqlChatBot
sdk: streamlit
emoji: 🚀
colorFrom: red
colorTo: yellow
short_description: Interact with a SQL database using natural language
---
# LangChain: Chat with SQL DB
This project is a Streamlit-based chatbot that allows you to interact with a SQL database (SQLite or MySQL) using natural language, powered by LangChain and LLMs (Groq API).


## Features
- Chat with your database using natural language queries
- Supports both SQLite (local) and MySQL (remote) databases
- Uses LangChain's SQL agent toolkit for intelligent query generation
- Streamlit UI for easy interaction
- Message history and conversation context

## Setup Instructions

### 1. Clone the repository
```
git clone https://github.com/Aarif-Mir/langchain-sql-chatbot.git
cd chatbot_sql
```

### 2. Install dependencies
It is recommended to use a virtual environment:
```
pip install -r requirements.txt
```

### 3. Prepare the database
- **SQLite (default):**
    - The project includes a sample `student.db` database. You can recreate it using `sqlite.py` if needed:
    ```
    python sqlite.py
    ```
- **MySQL:**
    - Make sure your MySQL server is running and you have the credentials (host, user, password, database name).

### 4. Get a Groq API Key
- Sign up at [Groq](https://console.groq.com/) and obtain your API key.

### 5. Run the Streamlit app
```
streamlit run app.py
```

## Usage
- Choose your database (SQLite or MySQL) from the sidebar.
- Enter your Groq API key in the sidebar.
- For MySQL, provide your connection details.
- Start chatting with your database!

## Notes
- The app uses the `Llama3-8b-8192` model via Groq.
- For SQLite, the app uses the included `student.db` file by default.
- For MySQL, you must provide all connection details.
- All dependencies are listed in `requirements.txt`.



