import streamlit as st
import google.generativeai as genai
import time
import os

# --- 1. PAGE CONFIGURATION & PREMIUM THEME ---
st.set_page_config(page_title="Fast&Up Pro Consult", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    /* Clean White App Background */
    .stApp { background-color: #FFFFFF; }
    
    /* Hide default Streamlit elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* THE LIGHT ORANGE CHAT CONTAINER */
    .block-container {
        background-color: #FFF8F0 !important; /* Light Orange / Peach */
        border-radius: 24px;
        box-shadow: 0px 10px 30px rgba(0, 32, 91, 0.08); /* Soft blue shadow */
        padding: 3rem 2rem !important;
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 1px solid #FFE0C2;
        max-width: 750px;
    }
    
    /* Title Styling */
    h1 { color: #FF5A00; text-align: center; font-weight: 800; padding-bottom: 0px; margin-bottom: 0px; font-size: 2.5rem;}
    .subtitle { text-align: center; color: #00205B; margin-bottom: 30px; font-weight: 600; letter-spacing: 1px;}
    
    /* WhatsApp Style Message Bubbles */
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 5px 0px !important; }
    
    /* USER BUBBLE (Fast&Up Blue) */
    .stChatMessage:has([data-testid="chatAvatarIcon-user"]) div[data-testid="stChatMessageContent"] {
        background-color: #00205B !important;
        color: #FFFFFF !important;
        border-radius: 18px 18px 0px 18px !important;
        padding: 12px 18px !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* AI BUBBLE (Clean White) */
    .stChatMessage:not(:has([data-testid="chatAvatarIcon-user"])) div[data-testid="stChatMessageContent"] {
        background-color: #FFFFFF !important;
        color: #00205B !important;
        border-radius: 18px 18px 18px 0px !important;
        padding: 12px 18px !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #F0F0F0;
    }
    
    /* Interactive Selection Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        border: 2px solid #FF5A00;
        color: #FF5A00;
        background-color: #FFFFFF;
        font-weight: bold;
        transition: all 0.3s ease;
        padding: 10px;
    }
    .stButton>button:hover { background-color: #FF5A00; color: #FFFFFF; transform: translateY(-2px); box-shadow: 0px 4px 10px rgba(255, 90, 0, 0.2); }
    
    /* Chat Input Area (Fixed styling) */
    [data-testid="stChatInput"] { background-color: #FFFFFF !important; border: 2px solid #FF5A00 !important; border-radius: 25px !important; }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: #FFFFFF; border-radius: 10px 10px 0px 0px; color: #00205B; font-weight: 600; padding: 10px 20px; border: 1px solid #FFE0C2; border-bottom: none;}
    .stTabs [aria-selected="true"] { background-color: #FF5A00 !important; color: #FFFFFF !important; border: 1px solid #FF5A00;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚡ Fast&Up</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Pro Nutrition AI Consultant</div>", unsafe_allow_html=True)

# --- 2. API SETUP & MODEL DETECTION ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("⚠️ Please add GEMINI_API_KEY to your Streamlit Secrets.")

@st.cache_resource
def get_working_model():
    """Dynamically finds the best model to prevent 404 errors."""
    try:
        valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if pref in valid_models: return pref
        return valid_models[0] if valid_models else "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

SYSTEM_PROMPT = """
You are the Fast&Up Premium Sports Nutrition AI Consultant.
1. Recommend ONLY Fast&Up products (e.g., Reload, BCAA, Charge, Plant Protein, Activate, Recover).
2. Never mention competitor brands.
3. Be concise, highly encouraging, and act like a professional nutritionist.
4. Base your recommendation strictly on the user's provided profile. Tell them EXACTLY why the product fits their needs.
"""

# --- 3. SESSION STATE (Button Logic) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to Fast&Up! ⚡ Let's find your perfect product.\n\n**To start, what is your primary fitness goal?**"}
    ]
if "chat_step" not in st.session_state:
    st.session_state.chat_step = 0 # 0:Goal, 1:Challenge, 2:Diet, 3:API Generation, 4:Open Chat
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}
if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []

# Helper function to move to the next question when a button is clicked
def advance_step(user_choice, next_bot_msg, profile_key):
    st.session_state.messages.append({"role": "user", "content": user_choice})
    st.session_state.user_profile[profile_key] = user_choice
    
    st.session_state.chat_step += 1
    if next_bot_msg:
        st.session_state.messages.append({"role": "assistant", "content": next_bot_msg})
    st.rerun()

# --- 4. FAQS DATA ---
FAQS = {
    "1. What is Fast&Up Reload?": "Reload is India’s first hypotonic effervescent hydration supplement with essential electrolytes and Vitamin C.",
    "2. How do I consume effervescent tablets?": "Drop 1 tablet in 250ml of water, wait for it to dissolve completely, and drink. Do not swallow the tablet directly.",
    "3. Are Fast&Up products Vegan?": "Yes! The vast majority of our products, including Reload, BCAA, and Plant Protein, are 100% vegan.",
    "4. When should I take Fast&Up BCAA?": "BCAA is best taken intra-workout (during your workout) to prevent muscle breakdown.",
    "5. What is Fast&Up Charge used for?": "Charge is a daily immunity booster featuring 1000mg of natural Amla extract (Vitamin C) and Zinc."
    # Add the rest of your 30 FAQs here!
}

# --- 5. TABS INTERFACE ---
tab1, tab2 = st.tabs(["💬 AI Consultant", "📚 Instant FAQs"])

with tab2:
    st.markdown("<h4 style='color:#00205B;'>Common Questions</h4>", unsafe_allow_html=True)
    for question, answer in FAQS.items():
        with st.expander(question):
            st.write(answer)

with tab1:
    # Render Chat History
    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else "⚡"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # --- THE DIAGNOSTIC BUTTON FLOW (0 Tokens) ---
    if st.session_state.chat_step == 0:
        st.write("") # Spacing
        col1, col2, col3 = st.columns(3)
        if col1.button("🏃‍♂️ Running / Cardio"): advance_step("Running / Cardio", "Got it! 💪\n\n**Next, what is the biggest challenge you face during your workouts?**", "Goal")
        if col2.button("🏋️‍♂️ Gym / Weights"): advance_step("Gym / Weightlifting", "Got it! 💪\n\n**Next, what is the biggest challenge you face during your workouts?**", "Goal")
        if col3.button("⚡ Daily Energy"): advance_step("Daily Health & Energy", "Got it! 💪\n\n**Next, what is the biggest challenge you face during your workouts?**", "Goal")

    elif st.session_state.chat_step == 1:
        st.write("")
        col1, col2, col3 = st.columns(3)
        if col1.button("😴 Fatigue / Tiredness"): advance_step("Fatigue", "Understood. 🥗\n\n**Finally, do you have any dietary preferences?**", "Challenge")
        if col2.button("🤕 Muscle Soreness"): advance_step("Muscle Soreness", "Understood. 🥗\n\n**Finally, do you have any dietary preferences?**", "Challenge")
        if col3.button("💧 Dehydration / Cramps"): advance_step("Dehydration", "Understood. 🥗\n\n**Finally, do you have any dietary preferences?**", "Challenge")

    elif st.session_state.chat_step == 2:
        st.write("")
        col1, col2, col3 = st.columns(3)
        if col1.button("🌱 Vegan / Plant-based"): advance_step("Vegan", None, "Diet")
        if col2.button("🚫 Sugar-Free"): advance_step("Sugar-Free", None, "Diet")
        if col3.button("🍽️ No Restrictions"): advance_step("No Restrictions", None, "Diet")

    # --- THE API GENERATION STEP ---
    elif st.session_state.chat_step == 3:
        with st.chat_message("assistant", avatar="⚡"):
            reply_placeholder = st.empty()
            reply_placeholder.markdown("*Analyzing your profile with Fast&Up Science...*")
            
            summary = f"Goal: {st.session_state.user_profile['Goal']}\nChallenge: {st.session_state.user_profile['Challenge']}\nDiet: {st.session_state.user_profile['Diet']}"
            api_prompt = f"SYSTEM INSTRUCTIONS:\n{SYSTEM_PROMPT}\n\nUSER PROFILE:\n{summary}\n\nBased strictly on this profile, recommend the perfect Fast&Up product and explain why."
            
            try:
                model = genai.GenerativeModel(model_name=get_working_model())
                st.session_state.gemini_history = [{"role": "user", "parts": [api_prompt]}]
                chat = model.start_chat(history=[])
                
                response = chat.send_message(api_prompt)
                
                # Smooth typing effect
                full_response = ""
                for chunk in response.text.split(" "):
                    full_response += chunk + " "
                    reply_placeholder.markdown(full_response + "▌")
                    time.sleep(0.03)
                reply_placeholder.markdown(full_response)
                
                st.session_state.gemini_history = chat.history
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                # Advance to step 4 to open the text box
                st.session_state.chat_step = 4
                time.sleep(1) # Brief pause before showing input box
                st.rerun()
            except Exception as e:
                reply_placeholder.markdown("⚠️ Could not connect to the API. Please ensure your API key has quota remaining.")

    # --- OPEN CHAT FOR FOLLOW UPS ---
    # The typing bar ONLY appears when step == 4
    elif st.session_state.chat_step == 4:
        if prompt := st.chat_input("Ask a follow-up question... (e.g., How do I use it?)"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="⚡"):
                reply_placeholder = st.empty()
                reply_placeholder.markdown("*Typing...*")
                try:
                    model = genai.GenerativeModel(model_name=get_working_model())
                    chat = model.start_chat(history=st.session_state.gemini_history)
                    
                    response = chat.send_message(prompt)
                    reply_placeholder.markdown(response.text)
                    
                    st.session_state.gemini_history = chat.history
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    reply_placeholder.markdown("⚠️ API Quota Exceeded. Please try again later.")
