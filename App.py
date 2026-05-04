import streamlit as st
import google.generativeai as genai
import time

# --- 1. PAGE CONFIGURATION & PREMIUM UI ---
st.set_page_config(page_title="Fast&Up Consultant", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stChatMessage { border-radius: 12px; padding: 15px; margin-bottom: 15px; border: 1px solid #2D3748; background-color: #1A202C; }
    [data-testid="chatAvatarIcon-user"] { background-color: #00ffd5; color: black; }
    h1 { color: #00ffd5; text-align: center; padding-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Fast&Up Pro Consultant")

# --- 2. THE DIAGNOSTIC API SETUP ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# This System Instruction forces the AI to ask questions before answering
diagnostic_prompt = """
You are a premium Fast&Up sports nutrition AI consultant. 
Your goal is to find the absolute perfect product match for the user by conducting a personalized consultation. 

CRITICAL RULES:
1. DO NOT recommend a product immediately.
2. You must ask the user the following 3 questions, but ask them strictly ONE AT A TIME. Wait for their answer before asking the next one.
   - Question 1: What is your primary fitness activity or goal? (e.g., running, gym, cycling, daily energy)
   - Question 2: What is your biggest challenge during or after this activity? (e.g., fatigue, muscle soreness, dehydration)
   - Question 3: Do you have any specific dietary preferences? (e.g., vegan, sugar-free)
3. Be conversational and energetic. Acknowledge their previous answer briefly before asking the next question.
4. Only AFTER you have gathered the answers to all 3 questions, analyze their profile and recommend the most suitable Fast&Up product (e.g., Reload, BCAA, Activate, Plant Protein). Explain exactly why it fits their specific needs based on their answers.
"""

expert_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=diagnostic_prompt
)

# --- 3. SESSION STATE MANAGEMENT ---
if "messages" not in st.session_state:
    # The AI starts the diagnostic flow immediately
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to Fast&Up! I'm your AI sports nutritionist. To find the perfect fuel for your body, I just need to ask you three quick questions.\n\nFirst, **what is your primary fitness activity or goal right now?**"}
    ]

if "gemini_history" not in st.session_state:
    # Initialize the history so the AI remembers the instructions and the first question
    st.session_state.gemini_history = [
        {"role": "model", "parts": ["Welcome to Fast&Up! I'm your AI sports nutritionist. To find the perfect fuel for your body, I just need to ask you three quick questions.\n\nFirst, **what is your primary fitness activity or goal right now?**"]}
    ]

# --- 4. RENDER CHAT HISTORY ---
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "⚡"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- 5. THE DYNAMIC CHAT LOGIC ---
if prompt := st.chat_input("Type your answer here..."):
    # 1. Show User Answer
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Trigger API to analyze the answer and ask the next question (or give the final result)
    with st.chat_message("assistant", avatar="⚡"):
        message_placeholder = st.empty()
        message_placeholder.markdown("*Analyzing...*")
        
        try:
            # We pass the history so the AI knows which question it's currently on!
            chat = expert_model.start_chat(history=st.session_state.gemini_history)
            response = chat.send_message(prompt)
            reply = response.text
            
            # Save the updated history back to the session state
            st.session_state.gemini_history = chat.history
            
        except Exception as e:
            reply = f"Error: Please ensure your API key is correct in the Streamlit settings."

        # 3. Stream the text smoothly
        full_response = ""
        for chunk in reply.split(" "):
            full_response += chunk + " "
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.02)
        message_placeholder.markdown(full_response)
        
    # 4. Save AI's response to UI state
    st.session_state.messages.append({"role": "assistant", "content": full_response})
