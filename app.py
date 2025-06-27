import streamlit as st
import requests
import json
from collections.abc import Generator

# --- Configuration ---
BASE_API_URL_GABU = "http://13.233.194.87:8000/gabu-nika-stream/"
BASE_API_URL_CHAT = "http://13.233.194.87:8000/chat-stream/"

# Models for each endpoint
GABU_MODELS = (
    "qwen_ft",
    # Add more gabu-nika-stream models here
)

CHAT_MODELS = (
    "deepseek_r1", "qwen3_235b", "deepseek_prover_671b", "llama_3_70b", "qwen_25_72b"
)

# Combine models for dropdown
ALL_MODELS = GABU_MODELS + CHAT_MODELS

# --- Page Setup ---
st.set_page_config(page_title="Model Testing UI", layout="centered")

# Set background colors for each part
st.markdown(
    """
    <style>
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: aquamarine; /* light bluish */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Model Testing UI 🤖")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = ALL_MODELS[0]

# --- Sidebar ---
with st.sidebar:
    st.header("Options")
    st.selectbox(
        "Choose a Model:",
        options=ALL_MODELS,
        key="selected_model"
    )
    clear_history = st.toggle("Start New Conversation", value=True)
    if st.button("Clear Chat Window"):
        st.session_state.messages = []
        st.rerun()

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Streaming Function ---
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
                yield f"Error: {response.status_code}\n{response.text}"
    except requests.exceptions.RequestException as e:
        yield f"Request Error: {e}"

# --- Chat Input Handling ---
if prompt := st.chat_input("What would you like to ask?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        selected_model = st.session_state.selected_model

        # Determine correct URL based on the selected model
        if selected_model in GABU_MODELS:
            api_url_to_use = f"{BASE_API_URL_GABU}{selected_model}"
        elif selected_model in CHAT_MODELS:
            api_url_to_use = f"{BASE_API_URL_CHAT}{selected_model}"
        else:
            st.error("Selected model is not configured correctly.")
            st.stop()

        response_generator = stream_response(prompt, clear_history, api_url_to_use)
        full_response = st.write_stream(response_generator)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

    if clear_history:
        pass
