"""
Enhanced SQL Chatbot
A Streamlit-based chatbot for interacting with SQL databases using natural language.
"""

import streamlit as st
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime

# LangChain imports
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine, text
import sqlite3
from langchain_groq import ChatGroq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
class DatabaseType:
    SQLITE = "SQLITE"
    MYSQL = "MYSQL"

class Config:
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    CACHE_TTL = 7200  # 2 hours in seconds
    MAX_QUERY_HISTORY = 50

def setup_page_config():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Enhanced SQL Chatbot",
        page_icon="🗄️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def validate_inputs(api_key: str, db_type: str, mysql_config: Dict[str, str] = None) -> tuple[bool, str]:
    """
    Validate user inputs and return validation status and error message.
    
    Args:
        api_key: Groq API key
        db_type: Database type (SQLITE or MYSQL)
        mysql_config: MySQL connection configuration
    
    Returns:
        Tuple of (is_valid, error_message
    """
    if not api_key or len(api_key.strip()) == 0:
        return False, "Please enter your Groq API key"
    
    if db_type == DatabaseType.MYSQL:
        required_fields = ['host', 'user', 'password', 'database']
        for field in required_fields:
            if not mysql_config.get(field) or len(mysql_config[field].strip()) == 0:
                return False, f"Please provide MySQL {field}"

    return True, ""

def get_database_config() -> tuple[str, Dict[str, str]]:
    """
    Get database configuration from user input.
    
    Returns:
        Tuple of (database_type, mysql_config)
    """
    st.sidebar.subheader("🗄️ Database Configuration")
    
    db_options = {
        "SQLite (Local)": DatabaseType.SQLITE,
        "MySQL (Remote)": DatabaseType.MYSQL
    }
    
    selected_db = st.sidebar.selectbox(
        "Choose Database Type:",
        options=list(db_options.keys()),
        help="Select your preferred database type"
    )
    
    db_type = db_options[selected_db]
    mysql_config = {}
    
    if db_type == DatabaseType.MYSQL:
        st.sidebar.subheader("MySQL Connection Details")
        mysql_config = {
            'host': st.sidebar.text_input("MySQL Host", placeholder="localhost"),
            'user': st.sidebar.text_input("MySQL Username"),
            'password': st.sidebar.text_input("MySQL Password", type="password"),
            'database': st.sidebar.text_input("MySQL Database Name")
        }
    
    return db_type, mysql_config

def get_api_config() -> str:
    """
    Get API configuration from user input.
    Returns:
        Groq API key
    """
    st.sidebar.subheader(" API Configuration")
    
    api_key = st.sidebar.text_input(
        "Groq API Key",
        type="password",
        help="Enter your Groq API key "
    )
    
    return api_key

@st.cache_resource(ttl=Config.CACHE_TTL)
def create_database_connection(db_type: str, mysql_config: Dict[str, str] = None) -> SQLDatabase:
    """
    Create and cache database connection.
    
    Args:
        db_type: Type of database (SQLITE or MYSQL)
        mysql_config: MySQL connection configuration
    
    Returns:
        SQLDatabase instance
    """
    try:
        if db_type == DatabaseType.SQLITE:
            db_file_path = (Path(__file__).parent / "student.db").absolute()
            
            if not db_file_path.exists():
                st.error(f" Database file not found: {db_file_path}")
                st.stop()
            
            creator = lambda: sqlite3.connect(f"file:{db_file_path}?mode=ro", uri=True)
            engine = create_engine("sqlite:///", creator=creator)
            
        elif db_type == DatabaseType.MYSQL:
            connection_string = (
                f"mysql+mysqlconnector://"
                f"{mysql_config['user']}:{mysql_config['password']}"
                f"@{mysql_config['host']}/{mysql_config['database']}"
            )
            engine = create_engine(connection_string)
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        db = SQLDatabase(engine)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info(f"Successfully connected to {db_type} database")
        return db
        
    except Exception as e:
        st.error(f" Database connection failed: {str(e)}")
        logger.error(f"Database connection error: {str(e)}")
        st.stop()

def display_database_info(db: SQLDatabase):
    """
    Display database schema and table information.
    
    Args:
        db: SQLDatabase instance
    """
    with st.expander(" Database Information", expanded=False):
        try:
            # Get table information
            tables = db.get_usable_table_names()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(" Tables")
                for table in tables:
                    st.write(f"• {table}")
            
            with col2:
                st.subheader(" Sample Data")
                if tables:
                    selected_table = st.selectbox("Select table to preview:", tables)
                    if selected_table:
                        try:
                            sample_query = f"SELECT * FROM {selected_table} LIMIT 5"
                            sample_df = pd.read_sql(sample_query, db._engine)
                            st.dataframe(sample_df, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error loading sample data: {str(e)}")
                            
        except Exception as e:
            st.error(f"Error loading database information: {str(e)}")

def create_agent(llm: ChatGroq, db: SQLDatabase) -> Any:
    """
    Create SQL agent with proper configuration.
    
    Args:
        llm: Language model instance
        db: Database instance
    
    Returns:
        Configured SQL agent
    """
    try:
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        
        agent = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=True,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            handle_parsing_errors=True,
        
        )
        
        return agent
        
    except Exception as e:
        st.error(f" Failed to create agent: {str(e)}")
        logger.error(f"Agent creation error: {str(e)}")
        st.stop()

def save_query_history(query: str, response: str):
    """Save query and response to session state history."""
    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.query_history.append({
        "timestamp": timestamp,
        "query": query,
        "response": response
    })
    
    # Keep only recent queries
    if len(st.session_state.query_history) > Config.MAX_QUERY_HISTORY:
        st.session_state.query_history = st.session_state.query_history[-Config.MAX_QUERY_HISTORY:]

def display_query_history():
    """Display query history in sidebar."""
    if "query_history" not in st.session_state or not st.session_state.query_history:
        return
    
    with st.sidebar.expander(" Query History", expanded=False):
        for i, entry in enumerate(reversed(st.session_state.query_history[-10:])):  # Show last 10
            with st.container():
                st.write(f"**{entry['timestamp']}**")
                st.write(f"**Q:** {entry['query'][:100]}{'...' if len(entry['query']) > 100 else ''}")
                st.write("---")

def main():
    """Main application function."""
    setup_page_config()
    
    # Header
    st.title("🗄️ Enhanced SQL Chatbot")
    st.markdown("Chat with your database using natural language queries powered by LangChain and Groq.")
    
    # Sidebar configuration
    db_type, mysql_config = get_database_config()
    api_key = get_api_config()
    
    # Display query history
    display_query_history()
    
    # Validation
    is_valid, error_message = validate_inputs(api_key, db_type, mysql_config)
    
    if not is_valid:
        st.error(f" {error_message}")
        st.stop()
    
    # Initialize components
    try:
        # Create LLM
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name=Config.DEFAULT_MODEL,
            streaming=True,
            temperature=0.1
        )
        
        # Test API key with a simple call
        try:
            llm.invoke("Hello")
        except Exception as e:
            st.error(" Please enter a valid Groq API key")
            st.stop()
        
        # Create database connection
        with st.spinner(" Connecting to database..."):
            db = create_database_connection(db_type, mysql_config)
        
        st.success(" Database connected successfully!")
        
        # Display database information
        display_database_info(db)
        
        # Create agent
        with st.spinner(" Initializing AI agent..."):
            agent = create_agent(llm, db)
        
        st.success(" AI agent ready!")
        
    except Exception as e:
        st.error(f" Initialization failed: {str(e)}")
        logger.error(f"Initialization error: {str(e)}")
        st.stop()
    
    # Chat interface
    st.subheader(" Chat with your Database")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": " Hello! I'm your SQL assistant. Ask me anything about your database!"
        }]
    
    # Clear chat button
    if st.sidebar.button(" Clear Chat History"):
        st.session_state.messages = [{
            "role": "assistant",
            "content": " Hello! I'm your SQL assistant. Ask me anything about your database!"
        }]
        st.rerun()
    # Clear query history only     
    if st.sidebar.button(" Clear Query History"):
        st.session_state.query_history = []
        st.rerun()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    user_query = st.chat_input(
        placeholder="Ask anything about your database (e.g., 'Show me all students with grade A')",
        disabled=not is_valid
    )
    
    if user_query:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_query)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            try:
                callback_handler = StreamlitCallbackHandler(st.container())
                with st.spinner(" Thinking..."):
                    # response = agent.run(user_query, callbacks=[callback_handler])
                    response = agent.invoke({"input": user_query}, callbacks=[callback_handler])
                    st.write(response)

                # Add assistant response to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                
                # Save to query history
                save_query_history(user_query, response)
                
            except Exception as e:
                error_msg = f" Error processing query: {str(e)}"
                st.error(error_msg)
                logger.error(f"Query processing error: {str(e)}")
                
                # Add error to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
    
    # Footer
    st.markdown("---")
    st.markdown(
        " **Tips:** "
        "• Be specific in your queries • Ask for data analysis or summaries • "
        "• Use natural language • Try queries like 'Show me the top 10 students'"
    )

if __name__ == "__main__":
    main()
