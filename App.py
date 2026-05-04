import streamlit as st
import google.generativeai as genai
import time

# --- 1. PAGE CONFIGURATION & PREMIUM UI ---
st.set_page_config(page_title="Fast&Up Consultant", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    /* Premium Dark Theme */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    
    /* Styled Chat Messages */
    .stChatMessage { border-radius: 12px; padding: 15px; margin-bottom: 15px; border: 1px solid #2D3748; background-color: #1A202C; }
    
    /* Highlight the User's messages slightly differently */
    [data-testid="chatAvatarIcon-user"] { background-color: #00ffd5; color: black; }
    
    /* Styled Buttons for Menu */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        border: 1px solid #00ffd5; 
        color: #00ffd5; 
        background-color: transparent; 
        font-weight: 600; 
        transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #00ffd5; color: #0E1117; transform: scale(1.02); }
    
    /* Typography */
    h1 { color: #00ffd5; text-align: center; padding-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Fast&Up Pro Consultant")

# --- 2. EXPERT CLOUD API SETUP (With Memory) ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# We create the model once
expert_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="You are a premium Fast&Up sports nutrition AI consultant. Be highly professional, concise, and energetic. Your goal is to guide users to the right product and prevent choice paralysis. Remember previous context in the conversation to handle follow-up questions effectively."
)

# --- 3. SESSION STATE MANAGEMENT ---
# Store UI messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Store Gemini API history for context/follow-ups
if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []

# --- 4. RENDER CHAT HISTORY ---
for msg in st.session_state.messages:
    # Use custom avatars
    avatar = "👤" if msg["role"] == "user" else "⚡"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- 5. TOKEN-SAVING LOCAL MENU (Zero API Usage) ---
# Only show the menu if the chat is empty
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant", avatar="⚡"):
        st.markdown("### Welcome to Fast&Up Nutrition!\nI am your AI consultant. To get started instantly, choose a category below, or type a custom question at the bottom.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💧 I need Hydration & Energy"):
                # Append user selection
                st.session_state.messages.append({"role": "user", "content": "I am looking for hydration and energy products."})
                # Append pre-written (free) AI response
                bot_reply = "Great! For instant hydration and electrolyte balance, I highly recommend **Fast&Up Reload**. \n\nIf you need a pre-workout energy boost, **Fast&Up Activate** is your best choice. \n\n*Would you like to know the ingredients of either of these, or compare them? Just ask below!*"
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                # Add to Gemini history so the AI knows what happened if they ask a follow-up
                st.session_state.gemini_history.extend([
                    {"role": "user", "parts": ["I am looking for hydration and energy products."]},
                    {"role": "model", "parts": [bot_reply]}
                ])
                st.rerun()
                
        with col2:
            if st.button("💪 I need Muscle Recovery"):
                st.session_state.messages.append({"role": "user", "content": "I am looking for muscle recovery products."})
                bot_reply = "Muscle soreness means you need amino acids! For post-workout recovery, **Fast&Up BCAA** is perfect to reduce muscle breakdown. \n\nWe also have **Fast&Up Plant Protein** if you are looking to build lean muscle. \n\n*Do you have any specific dietary restrictions I should know about?*"
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                st.session_state.gemini_history.extend([
                    {"role": "user", "parts": ["I am looking for muscle recovery products."]},
                    {"role": "model", "parts": [bot_reply]}
                ])
                st.rerun()

# --- 6. AI CHAT ROUTER (Handles custom questions & follow-ups) ---
if prompt := st.chat_input("Ask me anything about Fast&Up products..."):
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Trigger API for custom question
    with st.chat_message("assistant", avatar="⚡"):
        message_placeholder = st.empty()
        message_placeholder.markdown("*Consulting database...*")
        
        try:
            # Initialize chat session WITH history so it remembers previous questions
            chat = expert_model.start_chat(history=st.session_state.gemini_history)
            response = chat.send_message(prompt)
            reply = response.text
            
            # Update history in session state
            st.session_state.gemini_history = chat.history
            
        except Exception as e:
            reply = "I'm having trouble connecting right now. Please try again in a moment."

        # 3. Stream the response
        full_response = ""
        for chunk in reply.split(" "):
            full_response += chunk + " "
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.02)
        message_placeholder.markdown(full_response)
        
    # 4. Save to UI state
    st.session_state.messages.append({"role": "assistant", "content": full_response})
