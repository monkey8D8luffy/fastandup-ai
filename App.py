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
    
    /* Selection Buttons (Fast&Up Theme - 2x2 Grid Setup) */
    .stButton>button {
        width: 100%;
        border-radius: 16px;
        background-color: #FFFFFF !important;
        border: 2px solid #FF5A00 !important;
        color: #FF5A00 !important;
        font-weight: 700;
        transition: all 0.2s ease;
        padding: 12px 8px;
        margin-bottom: 8px;
        font-size: 0.95rem;
    }
    .stButton>button:hover { background-color: #FF5A00 !important; color: #FFFFFF !important; box-shadow: 0px 4px 10px rgba(255, 90, 0, 0.2); }
    
    /* Chat Input Area */
    [data-testid="stChatInput"] { background-color: #FFFFFF !important; border: 1px solid #D1D7DB !important; border-radius: 25px !important; }
    
    /* Tabs & Expander */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: #FFFFFF; border-radius: 10px 10px 0px 0px; border: 1px solid #D1D7DB; border-bottom: none;}
    .stTabs [aria-selected="true"] { background-color: #FF5A00 !important; }
    .stTabs [aria-selected="true"] p { color: #FFFFFF !important; font-weight: bold; }
    
    [data-testid="stExpander"] { background-color: #FFFFFF !important; border-radius: 10px; border: 1px solid #D1D7DB !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚡ Fast&Up</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Pro Nutrition AI Consultant</div>", unsafe_allow_html=True)

# --- 2. API SETUP (GROQ + Llama 3.3 70B) ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except KeyError:
    st.error("⚠️ Please add GROQ_API_KEY to your Streamlit Secrets.")

SYSTEM_PROMPT = """
You are the Fast&Up Premium Sports Nutrition AI Consultant.
1. Recommend ONLY Fast&Up products (e.g., Reload, BCAA, Charge, Plant Protein, Activate, Recover, Joint Care, Vitalize).
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
    st.session_state.api_history = [{"role": "system", "content": SYSTEM_PROMPT}]

def advance_step(user_choice, next_bot_msg, profile_key):
    st.session_state.messages.append({"role": "user", "content": user_choice})
    st.session_state.user_profile[profile_key] = user_choice
    st.session_state.chat_step += 1
    if next_bot_msg:
        st.session_state.messages.append({"role": "assistant", "content": next_bot_msg})
    st.rerun()

# --- 4. 30 INSTANT FAQS DATA ---
FAQS = {
    "1. What is Fast&Up Reload?": "Reload is India’s first hypotonic effervescent hydration supplement with essential electrolytes (Sodium, Potassium, Magnesium, Calcium) and Vitamin C.",
    "2. How do I consume effervescent tablets?": "Drop 1 tablet in 250ml of water, wait for it to dissolve completely, and drink. Do not swallow the tablet directly.",
    "3. Are Fast&Up products Vegan?": "Yes! The vast majority of our products, including Reload, BCAA, and Plant Protein, are 100% vegan and plant-based.",
    "4. When should I take Fast&Up BCAA?": "BCAA is best taken intra-workout (during your workout) or immediately after to prevent muscle breakdown and speed up recovery.",
    "5. What is Fast&Up Charge used for?": "Charge is a daily immunity booster featuring 1000mg of natural Amla extract (Vitamin C) and Zinc.",
    "6. What is the difference between Whey and Plant Protein?": "Whey is derived from milk, offering quick absorption. Plant Protein is derived from Pea and Brown Rice, perfect for vegans or those with lactose intolerance.",
    "7. Does Reload contain sugar?": "No! Fast&Up Reload contains zero added sugar, making it the perfect healthy hydration choice.",
    "8. Are your products tested for banned substances?": "Yes, our flagship sports range carries the elite 'Informed-Sport' certification, meaning every batch is tested for banned substances.",
    "9. Can I mix two Fast&Up tablets together?": "Yes! A popular combo is mixing 1 tablet of Reload with 1 tablet of BCAA in 500ml of water during heavy workouts.",
    "10. Do I need a prescription for Fast&Up?": "No, our products are nutritional health supplements and do not require a doctor's prescription.",
    "11. What is the shelf life of the products?": "Most of our products have a shelf life of 18-24 months from the date of manufacturing.",
    "12. How long does shipping take?": "Standard delivery takes 3-5 business days across India. Express delivery is available for select metro pincodes.",
    "13. Is Cash on Delivery (COD) available?": "Yes, COD is available across most pincodes in India.",
    "14. What is your return policy?": "We offer a 7-day replacement policy for damaged, missing, or incorrect products received.",
    "15. Can pregnant women consume Fast&Up?": "While safe, we always recommend pregnant or lactating women consult their physician before adding new supplements.",
    "16. Is Fast&Up suitable for children?": "Our sports range is formulated for adults (18+). However, we have a specific 'Fast&Up Kids' range formulated for younger needs.",
    "17. What is Fast&Up Activate?": "Activate is a pre-workout effervescent drink containing L-Arginine, L-Carnitine, and Zinc to boost blood flow and delay fatigue.",
    "18. What is Fast&Up Recover?": "Recover is a post-workout drink with a 3:1 Carbohydrate to Protein ratio, plus essential amino acids for complete muscle repair.",
    "19. How much water should I use?": "Generally, 250ml of water per tablet is recommended, but you can adjust slightly based on your taste preference.",
    "20. Where can I buy Fast&Up locally in Navi Mumbai?": "You can find our products at premium pharmacies like Wellness Forever in Sector 15, Kharghar, or order online for rapid delivery.",
    "21. Are there any artificial colors?": "No, we do not use banned artificial colors. We use natural food colorings.",
    "22. What should I take for joint pain?": "Fast&Up Joint Care contains Glucosamine, Chondroitin, and MSM to support cartilage health and joint mobility.",
    "23. Can I take vitamins on an empty stomach?": "While possible, taking multivitamins (like Vitalize) with a meal increases absorption and prevents mild nausea.",
    "24. Does Fast&Up have a loyalty program?": "Yes! Create an account on our website to earn 'F&U Coins' on every purchase which can be redeemed for discounts.",
    "25. Where are Fast&Up products manufactured?": "Our products are formulated with Swiss Technology and manufactured in world-class, FSSAI-compliant facilities in India.",
    "26. How do I track my order?": "You will receive a tracking link via SMS and Email as soon as your order is dispatched from our warehouse.",
    "27. Is the packaging recyclable?": "Yes, our plastic tubes and cardboard outer boxes are 100% recyclable.",
    "28. What if my effervescent tablet is broken?": "A broken tablet is perfectly safe to consume and will dissolve exactly the same way in water!",
    "29. Does Fast&Up offer running gels?": "Yes, we offer Energy Gels packed with fast-acting carbohydrates specifically designed for endurance runners and cyclists.",
    "30. How do I contact customer care?": "You can WhatsApp us at +91 9004044004 or email support@fastandup.in."
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

    # --- THE DIAGNOSTIC BUTTON FLOW (EXPANDED 2x2 GRID) ---
    if st.session_state.chat_step == 0:
        st.write("") 
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏃‍♂️ Endurance (Run/Cycle)"): advance_step("Endurance (Running/Cycling)", "Awesome! 🏃\n\n**Next, what is your biggest challenge or pain point?**", "Goal")
            if st.button("🛡️ Health & Immunity"): advance_step("Daily Health & Immunity", "Great choice! 🛡️\n\n**Next, what is your biggest challenge or pain point?**", "Goal")
        with col2:
            if st.button("🏋️‍♂️ Muscle Building (Gym)"): advance_step("Muscle Building (Gym)", "Let's get strong! 🏋️\n\n**Next, what is your biggest challenge or pain point?**", "Goal")
            if st.button("🦴 Joint Support & Flex"): advance_step("Joint Support & Flexibility", "Got it! 🦴\n\n**Next, what is your biggest challenge or pain point?**", "Goal")

    elif st.session_state.chat_step == 1:
        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("😴 Extreme Fatigue"): advance_step("Extreme Fatigue / Low Energy", "Understood. 🥗\n\n**Finally, do you have any dietary preferences?**", "Challenge")
            if st.button("💧 Dehydration / Cramps"): advance_step("Dehydration & Muscle Cramps", "Understood. 🥗\n\n**Finally, do you have any dietary preferences?**", "Challenge")
        with col2:
            if st.button("🤕 Slow Muscle Recovery"): advance_step("Muscle Soreness & Slow Recovery", "Understood. 🥗\n\n**Finally, do you have any dietary preferences?**", "Challenge")
            if st.button("🦠 Weak Immunity / Sick"): advance_step("Weak Immunity / Falling Sick Often", "Understood. 🥗\n\n**Finally, do you have any dietary preferences?**", "Challenge")

    elif st.session_state.chat_step == 2:
        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌱 100% Vegan"): advance_step("Strictly Vegan", None, "Diet")
            if st.button("🥛 Dairy-Tolerant (Whey)"): advance_step("Dairy-Tolerant (Can consume Whey)", None, "Diet")
        with col2:
            if st.button("🚫 Zero Added Sugar"): advance_step("Strictly Zero Added Sugar", None, "Diet")
            if st.button("🍽️ No Restrictions"): advance_step("No Restrictions", None, "Diet")

    # --- API GENERATION (GROQ Llama 3.3 70B) ---
    elif st.session_state.chat_step == 3:
        with st.chat_message("assistant", avatar="⚡"):
            reply_placeholder = st.empty()
            reply_placeholder.markdown("*Analyzing your precise profile with Fast&Up Science...*")
            
            summary = f"Goal: {st.session_state.user_profile['Goal']}\nChallenge: {st.session_state.user_profile['Challenge']}\nDiet: {st.session_state.user_profile['Diet']}"
            prompt = f"USER PROFILE:\n{summary}\n\nBased strictly on this profile, recommend the perfect Fast&Up product and explain why."
            
            st.session_state.api_history.append({"role": "user", "content": prompt})
            
            try:
                # Using the massive 70B model
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.api_history,
                    temperature=0.6,
                    max_tokens=350,
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

    # --- OPEN CHAT (Follow-ups) ---
    elif st.session_state.chat_step == 4:
        if prompt := st.chat_input("Ask a follow-up question... (e.g., When exactly should I drink this?)"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="⚡"):
                reply_placeholder = st.empty()
                reply_placeholder.markdown("*Typing...*")
                
                st.session_state.api_history.append({"role": "user", "content": prompt})
                
                try:
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=st.session_state.api_history,
                        temperature=0.6,
                        max_tokens=300,
                        stream=False
                    )
                    
                    final_reply = completion.choices[0].message.content
                    reply_placeholder.markdown(final_reply)
                    
                    st.session_state.api_history.append({"role": "assistant", "content": final_reply})
                    st.session_state.messages.append({"role": "assistant", "content": final_reply})
                except Exception as e:
                    reply_placeholder.markdown("⚠️ API connection issue. Please try again later.")
