import streamlit as st
from backend.core.db_manager import get_db

# Get the database instance
db = get_db()

st.title("Chat Example")

# Chat input
if input_message := st.chat_input(placeholder="Type something..."):
    try:
        # Insert the message using the database manager
        db.insert_message(input_message)
        st.success("Message saved successfully!")
    except Exception as e:
        st.error(f"Error saving message: {str(e)}")

# Display messages from the database
try:
    cursor = db.conn.execute(
        "SELECT message, created_at FROM messages ORDER BY created_at DESC LIMIT 10"
    )
    messages = cursor.fetchall()
    
    if messages:
        st.subheader("Recent Messages")
        for msg in messages:
            st.text(f"{msg['created_at']}: {msg['message']}")
    else:
        st.info("No messages yet. Type something in the chat!")
        
except Exception as e:
    st.error(f"Error fetching messages: {str(e)}") 