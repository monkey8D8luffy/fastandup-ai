import streamlit as st
import google.generativeai as genai
import os

# --- 1. PAGE CONFIGURATION & WHATSAPP UI THEME ---
st.set_page_config(page_title="Fast&Up AI Consult", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    /* App Background (WhatsApp Web Style Light Gray) */
    .stApp { background-color: #E5DDD5; }
    
    /* Hide default Streamlit headers/footers */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Fast&Up Title Styling */
    h1 { color: #FF5A00; text-align: center; font-family: 'Arial', sans-serif; font-weight: 800; margin-bottom: 0px; padding-bottom: 0px; }
    .subtitle { text-align: center; color: #00205B; margin-bottom: 20px; font-weight: 600; }
    
    /* Chat Message Container */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
        padding: 5px 0px !important;
    }
    
    /* USER BUBBLE (Fast&Up Blue) */
    .stChatMessage:has([data-testid="chatAvatarIcon-user"]) div[data-testid="stChatMessageContent"] {
        background-color: #00205B !important;
        color: #FFFFFF !important;
        border-radius: 15px 15px 0px 15px !important;
        padding: 12px 18px !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        display: inline-block;
        max-width: 85%;
        float: right;
    }
    
    /* AI BUBBLE (Clean White) */
    .stChatMessage:not(:has([data-testid="chatAvatarIcon-user"])) div[data-testid="stChatMessageContent"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 15px 15px 15px 0px !important;
        padding: 12px 18px !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        display: inline-block;
        max-width: 85%;
    }
    
    /* Chat Input Area */
    [data-testid="stChatInput"] {
        background-color: #FFFFFF !important;
        border: 2px solid #FF5A00 !important;
        border-radius: 25px !important;
    }
    [data-testid="stChatInput"] textarea { color: #000000 !important; }
    [data-testid="stChatInput"] button { color: #FF5A00 !important; }
    
    /* Tabs Styling (Fast&Up Theme) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF;
        border-radius: 10px 10px 0px 0px;
        color: #00205B;
        font-weight: 600;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #FF5A00 !important; color: #FFFFFF !important; }
    
    /* FAQ Expander */
    [data-testid="stExpander"] { background-color: #FFFFFF; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 5px; }
    [data-testid="stExpander"] p { color: #000000; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚡ Fast&Up</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Pro Nutrition AI Consultant</div>", unsafe_allow_html=True)

# --- 2. API SETUP & DYNAMIC MODEL SELECTION ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("⚠️ Please add GEMINI_API_KEY to your Streamlit Secrets.")

@st.cache_resource
def get_working_model():
    """Finds the best model available on your API key."""
    try:
        valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if pref in valid_models: return pref
        return valid_models[0] if valid_models else "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

SYSTEM_PROMPT = """
You are the Fast&Up Premium Sports Nutrition AI Consultant.
1. Recommend ONLY Fast&Up products (Reload, BCAA, Charge, Plant Protein, etc.).
2. Never mention competitor brands.
3. Be concise, friendly, and act like a professional nutritionist.
4. Base your final recommendation strictly on the user's provided profile.
"""

# --- 3. SESSION STATE (In-Chat Diagnostics) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to Fast&Up! ⚡ Let's find your perfect product. \n\n**To start, what is your primary fitness goal?** (e.g., Running, Gym, Daily Energy)"}
    ]
if "chat_step" not in st.session_state:
    st.session_state.chat_step = 0 # 0: Goal, 1: Challenge, 2: Diet, 3: AI Chat
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}
if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []

# --- 4. THE 30 INSTANT FAQs ---
FAQS = {
    "1. What is Fast&Up Reload?": "Reload is India’s first hypotonic effervescent hydration supplement with essential electrolytes (Sodium, Potassium, Magnesium, Calcium) and Vitamin C.",
    "2. How do I consume effervescent tablets?": "Drop 1 tablet in 250ml of water, wait for it to dissolve completely, and drink. Do not swallow the tablet directly.",
    "3. Are Fast&Up products Vegan?": "Yes! The vast majority of our products, including Reload, BCAA, and Plant Protein, are 100% vegan and plant-based.",
    "4. Is Fast&Up safe for everyday use?": "Yes, our daily nutrition range (like Charge, Reload, and Vitalize) is formulated for safe, everyday consumption.",
    "5. When should I take Fast&Up BCAA?": "BCAA is best taken intra-workout (during your workout) or immediately after to prevent muscle breakdown and speed up recovery.",
    "6. What is the difference between Whey and Plant Protein?": "Whey is derived from milk, offering quick absorption. Plant Protein is derived from Pea and Brown Rice, perfect for vegans or those with lactose intolerance.",
    "7. Does Reload contain sugar?": "No! Fast&Up Reload contains zero added sugar, making it the perfect healthy hydration choice.",
    "8. What is Fast&Up Charge used for?": "Charge is a daily immunity booster featuring 1000mg of natural Amla extract (Vitamin C) and Zinc.",
    "9. Are your products tested for banned substances?": "Yes, our flagship sports range carries the elite 'Informed-Sport' certification, meaning every batch is tested for banned substances.",
    "10. Can I mix two Fast&Up tablets together?": "Yes! A popular combo is mixing 1 tablet of Reload with 1 tablet of BCAA in 500ml of water during heavy workouts.",
    "11. Do I need a prescription for Fast&Up?": "No, our products are nutritional health supplements and do not require a doctor's prescription.",
    "12. What is the shelf life of the products?": "Most of our products have a shelf life of 18 months from the date of manufacturing.",
    "13. How long does shipping take?": "Standard delivery takes 3-5 business days across India. Express delivery is available for select metro pincodes.",
    "14. Is Cash on Delivery (COD) available?": "Yes, COD is available across most pincodes in India.",
    "15. What is your return policy?": "We offer a 7-day replacement policy for damaged, missing, or incorrect products received.",
    "16. Can pregnant women consume Fast&Up?": "While safe, we always recommend pregnant or lactating women consult their physician before adding new supplements.",
    "17. Is Fast&Up suitable for children?": "Our sports range is formulated for adults (18+). However, we have a specific 'Fast&Up Kids' range formulated for younger needs.",
    "18. What is Fast&Up Activate?": "Activate is a pre-workout effervescent drink containing L-Arginine, L-Carnitine, and Zinc to boost blood flow and delay fatigue.",
    "19. What is Fast&Up Recover?": "Recover is a post-workout drink with a 3:1 Carbohydrate to Protein ratio, plus essential amino acids for complete muscle repair.",
    "20. How much water should I use?": "Generally, 250ml of water per tablet is recommended, but you can adjust slightly based on your taste preference.",
    "21. Do you ship internationally?": "Currently, we ship widely across India. For international orders, please check our global partners or Amazon.",
    "22. Are there any artificial colors?": "No, we do not use banned artificial colors. We use natural food colorings.",
    "23. What should I take for joint pain?": "Fast&Up Joint Care contains Glucosamine, Chondroitin, and MSM to support cartilage health and joint mobility.",
    "24. Can I take vitamins on an empty stomach?": "While possible, taking multivitamins (like Vitalize) with a meal increases absorption and prevents mild nausea.",
    "25. Does Fast&Up have a loyalty program?": "Yes! Create an account on our website to earn 'F&U Coins' on every purchase which can be redeemed for discounts.",
    "26. Where are Fast&Up products manufactured?": "Our products are formulated with Swiss Technology and manufactured in world-class, FSSAI-compliant facilities in India.",
    "27. How do I track my order?": "You will receive a tracking link via SMS and Email as soon as your order is dispatched from our warehouse.",
    "28. Is the packaging recyclable?": "Yes, our plastic tubes and cardboard outer boxes are 100% recyclable.",
    "29. What if my effervescent tablet is broken?": "A broken tablet is perfectly safe to consume and will dissolve exactly the same way in water!",
    "30. How do I contact customer care?": "You can WhatsApp us at +91 9004044004 or email support@fastandup.in."
}

# --- 5. TABS INTERFACE ---
tab1, tab2 = st.tabs(["💬 AI Consultant", "FAQs"])

with tab2:
    st.markdown("### Common Questions")
    for question, answer in FAQS.items():
        with st.expander(question):
            st.write(answer)

with tab1:
    # Render Chat History
    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else "⚡"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Handle Input
    if prompt := st.chat_input("Type your message here..."):
        
        # 1. Display User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # 2. Local "Hi" Interceptor (0 Tokens Used)
        greetings = ["hi", "hello", "hey", "start", "good morning"]
        if prompt.lower().strip() in greetings and st.session_state.chat_step < 3:
            local_reply = "Hello! 👋 I'm ready to help. To give you the best recommendation, please answer the question above!"
            st.session_state.messages.append({"role": "assistant", "content": local_reply})
            with st.chat_message("assistant", avatar="⚡"):
                st.markdown(local_reply)
            st.rerun()

        # 3. Diagnostic State Machine (In-Chat)
        with st.chat_message("assistant", avatar="⚡"):
            reply_placeholder = st.empty()
            
            # STEP 0 -> STEP 1
            if st.session_state.chat_step == 0:
                st.session_state.user_profile['Goal'] = prompt
                bot_reply = "Got it! 💪 \n\n**Next, what is the biggest challenge you face during your workouts?** (e.g., Fatigue, Muscle Soreness, Dehydration)"
                st.session_state.chat_step = 1
                reply_placeholder.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
            # STEP 1 -> STEP 2
            elif st.session_state.chat_step == 1:
                st.session_state.user_profile['Challenge'] = prompt
                bot_reply = "Understood. 🥗 \n\n**Finally, do you have any dietary preferences?** (e.g., Vegan, Sugar-free, None)"
                st.session_state.chat_step = 2
                reply_placeholder.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
            # STEP 2 -> API CALL
            elif st.session_state.chat_step == 2:
                st.session_state.user_profile['Diet'] = prompt
                reply_placeholder.markdown("*Analyzing your profile with Fast&Up Science...*")
                
                summary = f"Goal: {st.session_state.user_profile['Goal']}\nChallenge: {st.session_state.user_profile['Challenge']}\nDiet: {st.session_state.user_profile['Diet']}"
                first_api_prompt = f"SYSTEM INSTRUCTIONS:\n{SYSTEM_PROMPT}\n\nUSER PROFILE:\n{summary}\n\nBased strictly on this profile, recommend the perfect Fast&Up product and explain why."
                
                try:
                    model = genai.GenerativeModel(model_name=get_working_model())
                    st.session_state.gemini_history = [{"role": "user", "parts": [first_api_prompt]}]
                    chat = model.start_chat(history=[])
                    
                    response = chat.send_message(first_api_prompt)
                    reply_placeholder.markdown(response.text)
                    
                    st.session_state.gemini_history = chat.history
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    st.session_state.chat_step = 3 # Move to open API chat
                except Exception as e:
                    reply_placeholder.markdown("⚠️ Could not connect to the API. Please ensure your key is valid.")
            
            # STEP 3+: OPEN API FOLLOW-UPS
            elif st.session_state.chat_step == 3:
                reply_placeholder.markdown("*Typing...*")
                try:
                    model = genai.GenerativeModel(model_name=get_working_model())
                    chat = model.start_chat(history=st.session_state.gemini_history)
                    
                    response = chat.send_message(prompt)
                    reply_placeholder.markdown(response.text)
                    
                    st.session_state.gemini_history = chat.history
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    reply_placeholder.markdown("⚠️ Could not connect to the API. Check your quota.")
