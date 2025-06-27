import streamlit as st
import requests
import json
from collections.abc import Generator

# --- Configuration ---
BASE_API_URL = "http://13.233.194.87:8000/gabu-nika-stream/"
BASE_API_URL_2 = "http://13.233.194.87:8000/chat-stream/"

MODEL_NAMES = (
    "qwen_ft",
    # Add more gabu-nika-stream models here
)

MODEL_NAMES_2 = (
    "deepseek_r1", "qwen3_235b", "deepseek_prover_671b", "llama_3_70b", "qwen_25_72b"
)

# Combine both for the dropdown with clear labels
MODEL_OPTIONS = (
    [f"{name}" for name in MODEL_NAMES] +
    [f"{name}" for name in MODEL_NAMES_2]
)

# --- Page Setup ---
st.set_page_config(page_title="Model Testing", layout="centered")
st.title("Model Testing UI")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = MODEL_OPTIONS[0]

# --- Sidebar for Options ---
with st.sidebar:
    st.header("Options")
    st.selectbox(
        "Choose a Model:",
        options=MODEL_OPTIONS,
        key="selected_model"
    )
    clear_history = st.toggle("Start New Conversation", value=True)
    if st.button("Clear Chat Window"):
        st.session_state.messages = []
        st.rerun()

# --- Chat Display ---
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

# --- User Input Handling ---
if prompt := st.chat_input("What would you like to ask?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Extract clean model name
        selected = st.session_state.selected_model
        if selected.startswith("[gabu-nika]"):
            model_name = selected.replace("[gabu-nika] ", "")
            api_url_to_use = f"{BASE_API_URL}{model_name}"
        elif selected.startswith("[chat-stream]"):
            model_name = selected.replace("[chat-stream] ", "")
            api_url_to_use = f"{BASE_API_URL_2}{model_name}"
        else:
            st.error("Invalid model selection.")
            st.stop()

        response_generator = stream_response(prompt, clear_history, api_url_to_use)
        full_response = st.write_stream(response_generator)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

    if clear_history:
        pass
