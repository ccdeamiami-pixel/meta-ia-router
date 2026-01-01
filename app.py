import streamlit as st
from openai import OpenAI
import urllib.parse
import speech_recognition as sr

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Meta-IA Router",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🧠 Meta-IA Router")
st.caption("La mejor IA del mercado, elegida para ti.")

# --- CONFIGURACIÓN API ---
api_key = st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    with st.sidebar:
        st.header("⚙️ Sistema")
        api_key = st.text_input("API Key (OpenRouter)", type="password")
        if not api_key:
            st.warning("⚠️ Modo Local: Ingresa tu API Key.")
            st.stop()
else:
    st.sidebar.success("✅ Sistema Conectado")

# --- CLIENTE ---
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

# --- HISTORIAL ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LÓGICA DE ROUTING ---
def select_best_model(user_query):
    query = user_query.lower()
    
    if any(word in query for word in ["imagen", "foto", "dibuja", "logo", "creativo visual", "dragon", "gato"]):
        return "image"
    elif any(word in query for word in ["código", "python", "javascript", "programar", "bug", "script", "función"]):
        return "code"
    else:
        return "text"

# --- ENTRADA POR VOZ O TEXTO ---
prompt = ""

# 1. Opción Voz (Nuevo!)
st.write("🎙️ Dicta tu consulta aquí:")
audio_file = st.audio_input("Grabar audio...")

if audio_file:
    with st.spinner("Escuchando y transcribiendo..."):
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                # Usamos Google Web Speech API (Gratuito)
                text_from_voice = recognizer.recognize_google(audio_data, language="es-ES")
                st.success(f"✅ Escuché: **{text_from_voice}**")
                prompt = text_from_voice
            except sr.UnknownValueError:
                st.error("No te entendí bien, intenta escribir.")
            except sr.RequestError:
                st.error("Error conectando con el servicio de voz.")

# 2. Opción Texto (Si no hubo voz, usa esto)
if not prompt:
    prompt = st.chat_input("Escribe tu consulta...")

# --- EJECUCIÓN ---
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    mode = select_best_model(prompt)

    with st.chat_message("assistant"):
        
        if mode == "image":
            st.caption("🎨 Generando imagen con Pollinations AI...")
            
            encoded_prompt = urllib.parse.quote(prompt)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed=random"
            
            try:
                st.image(image_url, caption=f"Prompt: {prompt}")
            except:
                st.markdown(f"### 🖼️ Tu Imagen")
                st.markdown(f"[Ver imagen]({image_url})")
            
            full_response = "Imagen generada."
            
        else:
            # TEXTO / CÓDIGO
            full_response = ""
            message_placeholder = st.empty()
            
            model_choice = "openai/gpt-4o" if mode == "text" else "anthropic/claude-3.5-sonnet"
            icon = "⚡" if mode == "text" else "💻"
            
            st.caption(f"{icon} {model_choice}")
            
            stream = client.chat.completions.create(
                model=model_choice,
                messages=[{"role": "system", "content": "Eres un asistente útil."}, {"role": "user", "content": prompt}],
                stream=True,
                max_tokens=800
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
