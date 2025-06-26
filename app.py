import streamlit as st
import requests
import json
from collections.abc import Generator

# --- Configuration --- _MODIFIED_
# 1. Define the base URL that is common to all your models.
BASE_API_URL = "http://13.233.194.87:8000/gabu-nika-stream/"

# 2. Create a list or tuple of the model names.
#    These are the names that will be appended to the base URL and shown in the dropdown.
MODEL_NAMES = (
    "qwen_ft",
     "llama3_ft_example",  # Example for another model
)
# To add a new model, just add its name to this tuple!

# --- Page Setup ---
st.set_page_config(page_title="Finetuned Model Chat", layout="centered")
st.title("Finetuned Model Chat")

# adding custom CSS to style the chat messages
st.markdown("""
    <style>
    .element-container .chat-message {
        background-color: rgba(221, 184, 31, 0.73);
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# _MODIFIED_: Initialize the selected model using the first name from our new list.
if "selected_model" not in st.session_state:
    st.session_state.selected_model = MODEL_NAMES[0]

# --- Sidebar for Options ---
with st.sidebar:
    st.header("Options")
    
    # _MODIFIED_: The dropdown now uses the simple MODEL_NAMES list.
    st.selectbox(
        "Choose a Model:",
        options=MODEL_NAMES,
        key="selected_model"
    )

    clear_history = st.toggle("Start New Conversation", value=True)
    
    if st.button("Clear Chat Window"):
        st.session_state.messages = []
        st.rerun()

# --- Chat Interface ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- The Core Logic: Function to Stream API Response ---
# This function no longer needs modification, it already accepts the full URL.
def stream_response(prompt: str, clear_history_flag: bool, api_url: str):
    headers = {
        "Content-Type": "application/json",
        "x-clear-history": "1" if clear_history_flag else "0"
    }
    data = {"prompt": prompt}
    
    try:
        with requests.post(api_url, headers=headers, json=data, stream=True, timeout=120) as response:
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=None):
                    if chunk:
                        yield chunk.decode('utf-8', errors='ignore')
            else:
                error_message = f"Error: {response.status_code}\n{response.text}"
                yield error_message
                
    except requests.exceptions.RequestException as e:
        yield f"Request Error: {e}"


# --- Handle User Input at the Bottom of the Page ---
if prompt := st.chat_input("What would you like to ask?"):
    
    # 1. Add the user's message to our history and display it.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Get the assistant's response.
    with st.chat_message("assistant"):
        # _MODIFIED_: Dynamically construct the full API URL here.
        selected_model_name = st.session_state.selected_model
        
        # Using an f-string to combine the base URL and the selected model name.
        api_url_to_use = f"{BASE_API_URL}{selected_model_name}"
        
        # Display the URL being used for debugging/confirmation (optional)
        # st.caption(f"Pinging endpoint: `{api_url_to_use}`")

        # Pass the fully constructed URL to the streaming function.
        response_generator = stream_response(prompt, clear_history, api_url_to_use)
        full_response = st.write_stream(response_generator)
    
    # 3. Add the full response from the assistant to our history.
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    if clear_history:
        pass