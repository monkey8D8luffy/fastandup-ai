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
    """Scan user input against FAQ patterns[span_3](start_span)[span_3](end_span)."""
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

_MODEL_NAME = "gemini-1.5-flash"

def get_gemini_recommendation(diagnostic_summary: str, chat_history: list[dict]) -> str:
    try:
        model = genai.GenerativeModel(model_name=_MODEL_NAME, system_instruction=_SYSTEM_PROMPT)
        history_payload = list(chat_history)
        if not history_payload:
            history_payload = [{
                "role": "user",
                "parts": [f"Here is my profile:\n{diagnostic_summary}\n\nBased on this, what Fast&Up products do you recommend?"]
            }]
        
        chat = model.start_chat(history=history_payload[:-1])
        result = chat.send_message(history_payload[-1]["parts"][0])
        return result.text
    except Exception as exc:
        return _offline_message(str(exc))

def get_gemini_followup(user_message: str, chat_history: list[dict]) -> str:
    try:
        model = genai.GenerativeModel(model_name=_MODEL_NAME, system_instruction=_SYSTEM_PROMPT)
        chat = model.start_chat(history=chat_history[:-1])
        result = chat.send_message(user_message)
        return result.text
    except Exception as exc:
        return _offline_message(str(exc))

def _offline_message(error: str = "") -> str:
    debug = f"\n\n*(Debug: {error[:120]})*" if os.getenv("FU_DEBUG") else ""
    return "**Heads up — our AI nutritionist is momentarily unavailable.**\n\nPlease reach us on WhatsApp at +91 9004044004." + debug
