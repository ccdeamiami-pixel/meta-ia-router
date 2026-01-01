import subprocess
import sys
import urllib.parse
import streamlit as st

# --- SOLUCIÓN EMERGENCIA: AUTO-INSTALACIÓN ---
# Si la nube no trae la librería OpenAI, se instala sola aquí.
try:
    from openai import OpenAI
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
    from openai import OpenAI

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
# Intenta buscar la llave en la Nube (Invisible) primero.
api_key = st.secrets.get("OPENROUTER_API_KEY")

# Si no la encuentra (ej: si estás en tu PC local), pide que la ingresen manualmente.
if not api_key:
    with st.sidebar:
        st.header("⚙️ Sistema")
        api_key = st.text_input("API Key (OpenRouter)", type="password")
        if not api_key:
            st.warning("⚠️ Modo Local: Ingresa tu API Key.")
            st.stop()
else:
    # Si la encontró en la nube, muestra un pequeño check verde pero oculto la clave.
    st.sidebar.success("✅ Sistema Conectado")

# --- CLIENTE ---
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

# --- HISTORIAL ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LÓGICA DE ROUTING AVANZADA ---
def select_best_model(user_query):
    query = user_query.lower()
    
    if any(word in query for word in ["imagen", "foto", "dibuja", "logo", "creativo visual", "dragon", "gato"]):
        return "image"
    elif any(word in query for word in ["código", "python", "javascript", "programar", "bug", "script", "función"]):
        return "code"
    else:
        return "text"

# --- EJECUCIÓN ---
if prompt := st.chat_input("Escribe tu consulta..."):
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
