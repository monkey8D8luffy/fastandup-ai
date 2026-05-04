import streamlit as st
import google.generativeai as genai
import time

# --- CONFIGURATION & UI ---
st.set_page_config(page_title="Fast&Up AI Prototype", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: white; }
    .stChatMessage { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px); border-radius: 15px; padding: 15px; margin-bottom: 10px; border: 1px solid rgba(255, 255, 255, 0.1); }
    .stButton>button { width: 100%; border-radius: 12px; border: 1px solid #00ffd5; color: #00ffd5; background: transparent; padding: 10px; }
    .stButton>button:hover { background: #00ffd5; color: black; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Fast&Up Hybrid AI Assistant")

# --- EXPERT CLOUD API SETUP ---
# It securely fetches your API key from Streamlit's secrets manager
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
expert_model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction="You are a Fast&Up expert. Help users prevent choice paralysis. If they need hydration, recommend 'Fast&Up Reload'. If they have muscle soreness, recommend 'Fast&Up BCAA'. Be energetic."
)

# --- SESSION STATE & CHAT UI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- INITIAL MENU ---
if len(st.session_state.messages) == 0:
    with st.chat_message("model"):
        st.markdown("Hello! I am your Fast&Up AI Assistant. How can I help you fuel your fitness today?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💧 Product for hydration"):
                st.session_state.messages.append({"role": "user", "content": "I need a product for hydration."})
                st.rerun()
        with col2:
            if st.button("💪 Product for muscle recovery"):
                st.session_state.messages.append({"role": "user", "content": "I need a product for muscle recovery."})
                st.rerun()

# --- CHAT INPUT & LOGIC ---
if prompt := st.chat_input("Or type your own question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("model"):
        message_placeholder = st.empty()
        message_placeholder.markdown("*Analyzing nutritional needs...*")
        
        try:
            response = expert_model.generate_content(prompt)
            reply = response.text
        except Exception as e:
            reply = "I'm having trouble connecting to my database right now!"

        full_response = ""
        for chunk in reply.split(" "):
            full_response += chunk + " "
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.03)
        message_placeholder.markdown(full_response)
        
    st.session_state.messages.append({"role": "model", "content": full_response})
