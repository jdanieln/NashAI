import streamlit as st
import requests
import json
import plotly.io as pio

# Page Config
st.set_page_config(page_title="NashAI", page_icon="🤖", layout="wide")

st.title("🤖 NashAI - Neuro-Symbolic Finance Agent")
st.markdown("Ask questions about your financial data in natural language.")

# Backend URL
API_URL = "http://localhost:8000/chat"

# Session State for History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "data" in msg:
            st.dataframe(msg["data"])
        if "plot" in msg:
            fig = pio.from_json(msg["plot"])
            st.plotly_chart(fig)

# User Input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call Backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(API_URL, json={"message": prompt})
                if response.status_code == 200:
                    data = response.json()["response"]
                    type_ = data.get("type", "unknown")
                    text_resp = data.get("text", "Done.")
                    
                    st.markdown(text_resp)
                    
                    msg_payload = {"role": "assistant", "content": text_resp}
                    
                    if type_ == "data":
                        st.dataframe(data["data"])
                        msg_payload["data"] = data["data"]
                        with st.expander("Show SQL"):
                            st.code(data.get("sql", ""))
                            
                    elif type_ == "plot":
                        fig_json = data["plot_json"]
                        fig = pio.from_json(fig_json)
                        st.plotly_chart(fig)
                        msg_payload["plot"] = fig_json
                        with st.expander("Show Code"):
                            st.code(data.get("code", ""))
                    
                    elif type_ == "error":
                        st.error(data.get("message"))
                    
                    st.session_state.messages.append(msg_payload)
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}. Is the backend running?")
