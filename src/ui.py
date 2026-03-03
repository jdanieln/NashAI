import streamlit as st
import requests
import json
import plotly.io as pio

# Page Config
st.set_page_config(page_title="NashAI", page_icon="🤖", layout="wide")

st.markdown("""
<style>
/* Alinear mensajes del usuario a la derecha (WhatsApp style) */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]),
div[data-testid="stChatMessage"]:has(svg[aria-label="user avatar"]),
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse;
}

/* Alinear el texto de los mensajes del usuario a la derecha */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stChatMessageContent"],
div[data-testid="stChatMessage"]:has(svg[aria-label="user avatar"]) div[data-testid="stChatMessageContent"],
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) div[data-testid="stChatMessageContent"] {
    align-items: flex-end;
    text-align: right;
}

/* Forzar el texto dentro del contenedor de Markdown */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] p,
div[data-testid="stChatMessage"]:has(svg[aria-label="user avatar"]) div[data-testid="stMarkdownContainer"] p,
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) div[data-testid="stMarkdownContainer"] p {
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 NashAI - Agente Financiero Neuro-Simbólico")
st.markdown("Haz preguntas sobre los datos financieros del BCIE en lenguaje natural.")

# Backend URL
API_URL = "http://localhost:8000/chat"

# Session State for History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg:
            with st.expander("Mostrar Consulta SQL"):
                st.code(msg["sql"], language="sql")
        if "data" in msg:
            st.dataframe(msg["data"])
        if "plot" in msg:
            fig_json_str = json.dumps(msg["plot"])
            fig = pio.from_json(fig_json_str)
            st.plotly_chart(fig)

# User Input
if prompt := st.chat_input("¿Qué te gustaría analizar u obtener de los datos?"):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call Backend
    with st.chat_message("assistant"):
        with st.spinner("Analizando..."):
            try:
                # Prepare history for the backend (excluding large data/plot objects to save payload size)
                trimmed_history = []
                for m in st.session_state.messages[:-1]: # exclude current prompt
                    trimmed_history.append({"role": m["role"], "content": m["content"]})
                
                response = requests.post(API_URL, json={
                    "message": prompt,
                    "history": trimmed_history
                })
                if response.status_code == 200:
                    data = response.json().get("response", {})
                    type_ = data.get("type", "unknown")
                    text_resp = data.get("text", "")
                    
                    if text_resp:
                        st.markdown(text_resp)
                    
                    msg_payload = {"role": "assistant", "content": text_resp}
                    
                    if type_ in ["data", "plot"]:
                        # Always show the SQL that generated the data
                        sql_str = data.get("sql", "")
                        if sql_str:
                            with st.expander("Mostrar Consulta SQL"):
                                st.code(sql_str, language="sql")
                            msg_payload["sql"] = sql_str
                            
                        # If plot requested, render it
                        if type_ == "plot" and "plot" in data:
                             fig_dict = data["plot"]
                             fig_json_str = json.dumps(fig_dict)
                             fig = pio.from_json(fig_json_str)
                             st.plotly_chart(fig)
                             msg_payload["plot"] = fig_dict
                             
                             if "code" in data:
                                 with st.expander("Mostrar Código del Gráfico (Python)"):
                                     st.code(data["code"], language="python")
                                     
                        # Fallback / explicit table rendering if 'data' array exists under either mode
                        if "data" in data:
                            with st.expander("Ver Tabla de Datos Crudos"):
                                st.dataframe(data["data"])
                            msg_payload["data"] = data["data"]
                            
                    elif type_ == "chat":
                        # Chat represents a conversational response handling only
                        pass # text already handled above
                        
                    elif type_ == "error":
                        error_msg = data.get("message", "Error desconocido")
                        st.error(error_msg)
                        msg_payload["content"] = error_msg
                        
                        sql_str = data.get("sql", "")
                        if sql_str:
                            with st.expander("Mostrar Consulta SQL Fallida"):
                                st.code(sql_str, language="sql")
                            msg_payload["sql"] = sql_str
                    
                    st.session_state.messages.append(msg_payload)
                else:
                    st.error(f"Error en servidor: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Fallo de conexión: {e}. ¿Está el backend (FastAPI) corriendo?")
