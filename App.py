from __future__ import annotations
import os
from pathlib import Path
import streamlit as st

from bot_logic import (
    build_diagnostic_summary,
    get_diagnostic_step,
    get_gemini_followup,
    get_gemini_recommendation,
    init_gemini,
    local_faq_lookup,
)

# --- Page Config ---
st.set_page_config(page_title="Fast&Up | AI Nutrition Expert", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- Inject CSS ---
_CSS_PATH = Path(__file__).parent / "style.css"
def _load_css() -> None:
    if _CSS_PATH.exists():
        css = _CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
_load_css()

# --- Gemini Initialisation ---
@st.cache_resource(show_spinner=False)
def _init_gemini_once(api_key: str) -> None:
    init_gemini(api_key)

def _get_api_key() -> str | None:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            return None
    return key or None

_api_key = _get_api_key()
if _api_key:
    _init_gemini_once(_api_key)

# --- Session State Bootstrap ---
DEFAULTS: dict = {
    "screen": "welcome",
    "faq_messages": [],
    "diag_goal": None,
    "diag_step": 0,
    "diag_answers": {},
    "diag_summary": "",
    "ai_messages": [],
    "gemini_history": [],
    "consult_started": False,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

def _go(screen: str) -> None:
    st.session_state["screen"] = screen
    st.rerun()

def _reset() -> None:
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.rerun()

def _append_gemini_history(role: str, text: str) -> None:
    st.session_state["gemini_history"].append({"role": role, "parts": [text]})

# --- Screens ---
def _screen_welcome() -> None:
    st.title("⚡ Fast&Up AI Expert")
    st.markdown("Your personal Fast&Up nutrition advisor.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 Instant FAQs", use_container_width=True):
            _go("faq_chat")
    with col2:
        if st.button("🤖 AI Consult", use_container_width=True):
            if not _api_key:
                st.error("API key missing. Set GEMINI_API_KEY.")
            else:
                _go("diag_goal")

def _screen_faq_chat() -> None:
    if st.button("← Back to Menu"):
        _reset()
    st.markdown("### 💬 Instant FAQ Answers")
    
    for msg in st.session_state["faq_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask about delivery, vegan products, stores..."):
        st.session_state["faq_messages"].append({"role": "user", "content": prompt})
        answer = local_faq_lookup(prompt)
        
        if answer:
            st.session_state["faq_messages"].append({"role": "assistant", "content": answer})
        else:
            st.session_state["faq_messages"].append({"role": "assistant", "content": "I don't have a ready answer for that. Try our AI Consult!"})
        st.rerun()

def _screen_diag_goal() -> None:
    if st.button("← Back"): _reset()
    st.markdown("### Step 1: What is your primary goal?")
    GOALS = ["Hydration / Energy", "Muscle Building / Recovery"]
    
    goal = st.radio("Select your goal:", options=GOALS, label_visibility="collapsed")
    if st.button("Continue", use_container_width=True):
        st.session_state["diag_goal"] = goal
        st.session_state["diag_step"] = 0
        st.session_state["diag_answers"] = {}
        _go("diag_steps")

def _screen_diag_steps() -> None:
    goal = st.session_state["diag_goal"]
    step_index = st.session_state["diag_step"]
    from bot_logic import DIAGNOSTIC_STEPS
    total_steps = len(DIAGNOSTIC_STEPS.get(goal, []))
    
    step = get_diagnostic_step(goal, step_index)
    if step is None:
        answers = st.session_state["diag_answers"]
        st.session_state["diag_summary"] = build_diagnostic_summary(goal, answers)
        _go("ai_chat")
        return

    st.progress((step_index) / total_steps, text=f"Question {step_index + 1}/{total_steps}")
    st.markdown(f"### {step['question']}")
    
    chosen = st.radio("Choose one:", options=step["options"], label_visibility="collapsed")
    
    if st.button("Next ➔", use_container_width=True):
        st.session_state["diag_answers"][step["key"]] = chosen
        st.session_state["diag_step"] += 1
        st.rerun()

def _screen_ai_chat() -> None:
    if st.button("← Start Over"): _reset()
    st.markdown("### 🤖 Fast&Up AI Recommendation")
    
    if not st.session_state["consult_started"]:
        st.session_state["consult_started"] = True
        summary = st.session_state["diag_summary"]
        
        st.session_state["ai_messages"].append({"role": "user", "content": f"**My Profile:**\n{summary}"})
        seed_turn = {"role": "user", "parts": [f"Profile:\n{summary}\n\nWhat Fast&Up products do you recommend?"]}
        st.session_state["gemini_history"] = [seed_turn]
        
        with st.spinner("Analyzing..."):
            reply = get_gemini_recommendation(summary, [seed_turn])
            st.session_state["ai_messages"].append({"role": "assistant", "content": reply})
            _append_gemini_history("model", reply)
            st.rerun()

    for msg in st.session_state["ai_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask a follow up..."):
        st.session_state["ai_messages"].append({"role": "user", "content": prompt})
        _append_gemini_history("user", prompt)
        
        with st.spinner("Thinking..."):
            reply = get_gemini_followup(prompt, st.session_state["gemini_history"])
            st.session_state["ai_messages"].append({"role": "assistant", "content": reply})
            _append_gemini_history("model", reply)
        st.rerun()

# --- Router ---
def main() -> None:
    screen = st.session_state["screen"]
    if screen == "welcome": _screen_welcome()
    elif screen == "faq_chat": _screen_faq_chat()
    elif screen == "diag_goal": _screen_diag_goal()
    elif screen == "diag_steps": _screen_diag_steps()
    elif screen == "ai_chat": _screen_ai_chat()

if __name__ == "__main__":
    main()
