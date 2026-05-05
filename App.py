import streamlit as st
from groq import Groq
import time

# --- 1. PAGE CONFIGURATION & WHATSAPP-STYLE UI ---
st.set_page_config(page_title="Fast&Up Pro Consult", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    /* Force Light Mode styling regardless of device theme */
    .stApp { background-color: #F0F2F5 !important; }
    
    /* Hide Streamlit elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Ensure all text is dark and readable */
    p, h1, h2, h3, h4, h5, h6, span, div, li { color: #111B21 !important; }
    
    /* The Chat Container Wrapper */
    .block-container {
        background-color: #EFEAE2 !important; /* WhatsApp Chat Background */
        border-radius: 16px;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.08);
        padding: 2rem 1.5rem !important;
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 1px solid #D1D7DB;
        max-width: 750px;
    }
    
    /* Fast&Up Branding Headers */
    h1 { color: #FF5A00 !important; text-align: center; font-weight: 800; padding-bottom: 0px; margin-bottom: 0px; font-size: 2.2rem;}
    .subtitle { text-align: center; color: #00205B !important; margin-bottom: 30px; font-weight: 600; letter-spacing: 0.5px;}
    
    /* Chat Message Base */
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 5px 0px !important; }
    
    /* USER BUBBLE (WhatsApp Green) */
    [data-testid="stChatMessage"][data-testid*="user"] div[data-testid="stChatMessageContent"] {
        background-color: #D9FDD3 !important;
        color: #111B21 !important;
        border-radius: 12px 0px 12px 12px !important;
        padding: 10px 15px !important;
        box-shadow: 0 1px 2px rgba(11,20,26,0.1) !important;
    }
    
    /* AI BUBBLE (Clean White) */
    [data-testid="stChatMessage"]:not([data-testid*="user"]) div[data-testid="stChatMessageContent"] {
        background-color: #FFFFFF !important;
        color: #111B21 !important;
        border-radius: 0px 12px 12px 12px !important;
        padding: 10px 15px !important;
        box-shadow: 0 1px 2px rgba(11,20,26,0.1) !important;
    }
    
    /* Selection Buttons (Fast&Up Theme) */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #FFFFFF !important;
        border: 2px solid #FF5A00 !important;
        color: #FF5A00 !important;
        font-weight: bold;
        transition: all 0.2s ease;
        padding: 8px;
    }
    .stButton>button:hover { background-color: #FF5A00 !important; color: #FFFFFF !important; box-shadow: 0px 4px 10px rgba(255, 90, 0, 0.2); }
    
    /* Chat Input Area */
    [data-testid="stChatInput"] { background-color: #FFFFFF !important; border: 1px solid #D1D7DB !important; border-radius: 25px !important; }
    
    /* Tabs & Expander (Fixing invisible text) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: #FFFFFF; border-radius: 10px 10px 0px 0px; border: 1px solid #D1D7DB; border-bottom: none;}
    .stTabs [aria-selected="true"] { background-color: #FF5A00 !important; }
    .stTabs [aria-selected="true"] p { color: #FFFFFF !important; font-weight: bold; }
    
    [data-testid="stExpander"] { background-color: #FFFFFF !important; border-radius: 10px; border: 1px solid #D1D7DB !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚡ Fast&Up</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Pro Nutrition AI Consultant</div>", unsafe_allow_html=True)

# --- 2. API SETUP (GROQ + Llama 3) ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except KeyError:
    st.error("⚠️ Please add GROQ_API_KEY to your Streamlit Secrets.")

SYSTEM_PROMPT = """
You are the Fast&Up Premium Sports Nutrition AI Consultant.
1. Recommend ONLY Fast&Up products (e.g., Reload, BCAA, Charge, Plant Protein, Activate, Recover).
2. Never mention competitor brands.
3. Be concise, highly encouraging, and act like a professional nutritionist.
4. Base your recommendation strictly on the user's provided profile. Tell them EXACTLY why the product fits their needs.
"""

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to Fast&Up! ⚡ Let's find your perfect product.\n\n**To start, what is your primary fitness goal?**"}
    ]
if "chat_step" not in st.session_state:
    st.session_state.chat_step = 0 
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}
if "api_history" not in st.session_state:
    # Initialize Groq history format
    st.session_state.api_history = [{"role": "system", "content": SYSTEM_PROMPT}]

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
}

# --- 5. TABS INTERFACE ---
tab1, tab2 = st.tabs(["💬 AI Consultant", "📚 Instant FAQs"])

with tab2:
    st.markdown("<h4 style='color:#00205B !important;'>Common Questions</h4>", unsafe_allow_html=True)
    for question, answer in FAQS.items():
        with st.expander(question):
            st.write(answer)

with tab1:
    # Render Chat History
    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else "⚡"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # --- THE DIAGNOSTIC BUTTON FLOW ---
    if st.session_state.chat_step == 0:
        st.write("") 
        col1, col2, col3 = st.columns(3)
        if col1.button("🏃‍♂️ Running/Cardio"): advance_step("Running / Cardio", "Got it! 💪\n\n**Next, what is your biggest challenge?**", "Goal")
        if col2.button("🏋️‍♂️ Gym/Weights"): advance_step("Gym / Weightlifting", "Got it! 💪\n\n**Next, what is your biggest challenge?**", "Goal")
        if col3.button("⚡ Daily Energy"): advance_step("Daily Health & Energy", "Got it! 💪\n\n**Next, what is your biggest challenge?**", "Goal")

    elif st.session_state.chat_step == 1:
        st.write("")
        col1, col2, col3 = st.columns(3)
        if col1.button("😴 Fatigue"): advance_step("Fatigue", "Understood. 🥗\n\n**Finally, any dietary preferences?**", "Challenge")
        if col2.button("🤕 Soreness"): advance_step("Muscle Soreness", "Understood. 🥗\n\n**Finally, any dietary preferences?**", "Challenge")
        if col3.button("💧 Dehydration"): advance_step("Dehydration", "Understood. 🥗\n\n**Finally, any dietary preferences?**", "Challenge")

    elif st.session_state.chat_step == 2:
        st.write("")
        col1, col2, col3 = st.columns(3)
        if col1.button("🌱 Vegan"): advance_step("Vegan", None, "Diet")
        if col2.button("🚫 Sugar-Free"): advance_step("Sugar-Free", None, "Diet")
        if col3.button("🍽️ None"): advance_step("No Restrictions", None, "Diet")

    # --- API GENERATION (GROQ) ---
    elif st.session_state.chat_step == 3:
        with st.chat_message("assistant", avatar="⚡"):
            reply_placeholder = st.empty()
            reply_placeholder.markdown("*Analyzing your profile with Fast&Up Science...*")
            
            summary = f"Goal: {st.session_state.user_profile['Goal']}\nChallenge: {st.session_state.user_profile['Challenge']}\nDiet: {st.session_state.user_profile['Diet']}"
            prompt = f"USER PROFILE:\n{summary}\n\nBased strictly on this profile, recommend the perfect Fast&Up product and explain why."
            
            st.session_state.api_history.append({"role": "user", "content": prompt})
            
            try:
                # Groq API Call
                completion = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=st.session_state.api_history,
                    temperature=0.6,
                    max_tokens=300,
                    stream=False
                )
                
                final_reply = completion.choices[0].message.content
                reply_placeholder.markdown(final_reply)
                
                st.session_state.api_history.append({"role": "assistant", "content": final_reply})
                st.session_state.messages.append({"role": "assistant", "content": final_reply})
                
                st.session_state.chat_step = 4
                time.sleep(1) 
                st.rerun()
            except Exception as e:
                reply_placeholder.markdown(f"⚠️ Could not connect to the API. Please ensure your GROQ_API_KEY is valid. Error: {e}")

    # --- OPEN CHAT ---
    elif st.session_state.chat_step == 4:
        if prompt := st.chat_input("Ask a follow-up question... (e.g., How do I use it?)"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="⚡"):
                reply_placeholder = st.empty()
                reply_placeholder.markdown("*Typing...*")
                
                st.session_state.api_history.append({"role": "user", "content": prompt})
                
                try:
                    completion = client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=st.session_state.api_history,
                        temperature=0.6,
                        max_tokens=250,
                        stream=False
                    )
                    
                    final_reply = completion.choices[0].message.content
                    reply_placeholder.markdown(final_reply)
                    
                    st.session_state.api_history.append({"role": "assistant", "content": final_reply})
                    st.session_state.messages.append({"role": "assistant", "content": final_reply})
                except Exception as e:
                    reply_placeholder.markdown("⚠️ API Quota Exceeded. Please try again later.")
