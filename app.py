import streamlit as st
import requests
import json
from collections.abc import Generator

# --- Configuration ---
# This is the URL of the API you are testing.
API_URL = "http://13.233.194.87:8000/gabu-nika-stream/qwen_ft"

# --- Page Setup ---
# Set the title and icon that appear in the browser tab.
st.set_page_config(page_title="Finetuned Model chat", layout="centered")
# The main title of the web page.
st.title("Finetuned Model chat")

# --- Session State Initialization ---
# "Session state" is Streamlit's way of remembering things.
# We initialize a "messages" list to store the chat history.
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar for Options ---
# "with st.sidebar:" puts the following elements in a collapsible sidebar.
with st.sidebar:
    st.header("Options")
    # A toggle switch. 'value=True' means it's ON by default.
    # This will control our 'x-clear-history' header.
    clear_history = st.toggle("Start New Conversation", value=True)
    
    # A button to manually clear the chat displayed on the screen.
    if st.button("Clear Chat Window"):
        st.session_state.messages = []
        st.rerun() # Rerun the app to reflect the change.


# --- Chat Interface ---
# Display all the past messages stored in our session state.
for message in st.session_state.messages:
    # "with st.chat_message(...)" creates the nice chat bubbles.
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- The Core Logic: Function to Stream API Response ---
# This function calls your API and yields the response piece by piece.
def stream_response(prompt, clear_history_flag):
    headers = {
        "Content-Type": "application/json",
        # Set 'x-clear-history' to "1" if the toggle is on, otherwise "0".
        "x-clear-history": "1" if clear_history_flag else "0"
    }
    data = {"prompt": prompt}
    
    try:
        # requests.post with stream=True keeps the connection open.
        with requests.post(API_URL, headers=headers, json=data, stream=True, timeout=120) as response:
            if response.status_code == 200:
                # We read the response in chunks.
                # Your API might send data in a different format. This assumes raw text.
                for chunk in response.iter_content(chunk_size=None):
                    if chunk:
                        # 'yield' sends one piece of data back at a time.
                        yield chunk.decode('utf-8', errors='ignore')
            else:
                # If there's an error, yield the error message.
                error_message = f"Error: {response.status_code}\n{response.text}"
                yield error_message
                
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, etc.
        yield f"Request Error: {e}"


# --- Handle User Input at the Bottom of the Page ---
# "st.chat_input" creates the text box at the bottom.
# The 'if prompt :=' syntax is a neat way to check if the user entered something.
if prompt := st.chat_input("What would you like to ask?"):
    
    # 1. Add the user's message to our history and display it.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Get the assistant's response.
    with st.chat_message("assistant"):
        # This is the magic! st.write_stream takes our streaming function
        # and automatically displays the output as it arrives.
        response_generator = stream_response(prompt, clear_history)
        full_response = st.write_stream(response_generator)
    
    # 3. Add the full response from the assistant to our history.
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # 4. A small bit of logic to automatically turn off the "New Conversation"
    #    toggle after the first message is sent.
    if clear_history:
        # This part requires a bit more complex state management, but for now
        # we can just let the user untoggle it manually for the next message.
        # For a better UX, you would manage the toggle state more actively.
        # Let's keep it simple for now. The user can just un-toggle it.
        pass