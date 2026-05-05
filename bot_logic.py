from __future__ import annotations
import os
import re
import textwrap
from typing import Optional
import google.generativeai as genai

# --- 0. Gemini Initialisation ---
def init_gemini(api_key: str) -> None:
    """Configure the Gemini SDK once at startup."""
    genai.configure(api_key=api_key)

# --- NEW: Auto-Detect Best Working Model ---
_WORKING_MODEL = None

def get_working_model() -> str:
    """Dynamically asks Google's servers which models your API key has access to."""
    global _WORKING_MODEL
    if _WORKING_MODEL:
        return _WORKING_MODEL
    
    try:
        # Call ListModels just like the error message suggested!
        valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Rank our preferences from newest to oldest
        preferences = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro', 'models/gemini-1.0-pro']
        
        for pref in preferences:
            if pref in valid_models:
                _WORKING_MODEL = pref
                return _WORKING_MODEL
                
        # If none of our preferences match, just grab the first valid text model available
        if valid_models:
            _WORKING_MODEL = valid_models[0]
            return _WORKING_MODEL
    except Exception:
        pass
        
    return "models/gemini-1.5-flash" # Absolute fallback

# --- 1. Local FAQ Dictionary & Router (ZERO API TOKENS) ---
FAQ_DB: list[tuple[list[str], str]] = [
    (
        [r"\bvegan\b", r"\bvegetarian\b", r"\bplant.based\b", r"\banimal.free\b"],
        "**Yes! Fast&Up has a dedicated vegan range!**\n\n"
        "- **Reload** (electrolyte tablet) is 100% vegan\n"
        "- **BCAA** is available in a vegan-certified variant\n"
        "- **Charge** (Vitamin C + Zinc effervescent) is vegan\n"
        "- **Promega** (Omega-3 from algae) is fully plant-based"
    ),
    (
        [r"\bkharghar\b", r"\bnavi\s?mumbai\b"],
        "**Fast&Up stores near Kharghar, Navi Mumbai:**\n\n"
        "1. **Fast&Up Exclusive Store** - Sector 20, Kharghar\n"
        "2. **GNC Partner Store** - Inorbit Mall, Vashi (8 km)\n"
        "3. **Wellness Forever** - Sector 15, Kharghar\n\n"
        "You can also order with same-day delivery on the Fast&Up app."
    ),
    (
        [r"\breload\b", r"\belectrolyte\b", r"\bsports drink\b"],
        "**Fast&Up Reload Electrolyte Tablet:**\n\n"
        "- Effervescent tablet; just drop in 250 ml water.\n"
        "- Contains **Na, K, Mg, Ca** + Vitamin C.\n"
        "- Zero sugar, 11 cal/tablet.\n"
        "- Ideal before, during, or after exercise."
    )
]

def local_faq_lookup(user_input: str) -> Optional[str]:
    """Scan user input against FAQ patterns."""
    text = user_input.lower().strip()
    for patterns, answer in FAQ_DB:
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return answer
    return None

# --- 2. Diagnostic Questionnaire (Zero API Tokens) ---
DIAGNOSTIC_STEPS = {
    "Hydration / Energy": [
        {"key": "activity", "question": "How active are you?", "options": ["Sedentary", "Moderately active", "Highly active"]},
        {"key": "sweat", "question": "How much do you typically sweat?", "options": ["Light sweater", "Moderate sweater", "Heavy sweater"]},
        {"key": "diet", "question": "How would you describe your diet?", "options": ["Balanced", "Mostly vegetarian / vegan", "Keto / Low-carb"]}
    ],
    "Muscle Building / Recovery": [
        {"key": "training", "question": "What type of training do you do?", "options": ["Strength / Weightlifting", "Endurance", "Mixed"]},
        {"key": "protein_intake", "question": "How is your daily protein intake?", "options": ["Below target", "Moderate", "High"]},
        {"key": "recovery", "question": "How is your post-workout recovery?", "options": ["Poor - very sore", "Average", "Quick recovery"]}
    ]
}

def get_diagnostic_step(goal: str, step_index: int) -> Optional[dict]:
    steps = DIAGNOSTIC_STEPS.get(goal, [])
    if step_index < len(steps):
        return steps[step_index]
    return None

def build_diagnostic_summary(goal: str, answers: dict[str, str]) -> str:
    lines = [f"**Goal:** {goal}"]
    steps = DIAGNOSTIC_STEPS.get(goal, [])
    for step in steps:
        key = step["key"]
        if key in answers:
            lines.append(f"**{step['question']}** {answers[key]}")
    return "\n".join(lines)

# --- 3. System Prompt & Gemini API ---
_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a knowledgeable, warm, and enthusiastic product expert for Fast&Up.
    RULES YOU MUST FOLLOW:
    1. Recommend ONLY Fast&Up products.
    2. Never recommend, compare, or mention competitor brands. Pivot back to Fast&Up gently.
    3. Be concise (under 200 words).
    4. Base recommendations strictly on the user's provided diagnostic profile.
""")

def get_gemini_recommendation(diagnostic_summary: str, chat_history: list[dict]) -> str:
    try:
        model = genai.GenerativeModel(model_name=get_working_model())
        history_payload = list(chat_history)
        
        # Inject the strict Fast&Up brand guardrails directly into the first prompt
        # This completely bypasses the SDK versioning bugs causing the 404 errors!
        if history_payload and "SYSTEM INSTRUCTIONS" not in history_payload[0]["parts"][0]:
            history_payload[0]["parts"][0] = f"SYSTEM INSTRUCTIONS:\n{_SYSTEM_PROMPT}\n\n" + history_payload[0]["parts"][0]
            # Update the original history so Streamlit remembers the rules
            chat_history[0]["parts"][0] = history_payload[0]["parts"][0]
            
        chat = model.start_chat(history=history_payload[:-1])
        result = chat.send_message(history_payload[-1]["parts"][0])
        return result.text
    except Exception as exc:
        return _offline_message(str(exc))

def get_gemini_followup(user_message: str, chat_history: list[dict]) -> str:
    try:
        model = genai.GenerativeModel(model_name=get_working_model())
        chat = model.start_chat(history=chat_history[:-1])
        result = chat.send_message(user_message)
        return result.text
    except Exception as exc:
        return _offline_message(str(exc))

def _offline_message(error: str = "") -> str:
    debug = f"\n\n*(Debug: {error[:120]})*" if os.getenv("FU_DEBUG") else ""
    return "**Heads up — our AI nutritionist is momentarily unavailable.**\n\nPlease reach us on WhatsApp at +91 9004044004." + debug
