from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import google.generativeai as genai
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# ১. কনফিগারেশন ও মডেল অপশন (সঠিক ও সমর্থিত জেমিনি মডেলসমূহ)
# ==============================================================================
DATA_FILE = "gemini_workspace_data.json"
LOCAL_KEY_FILE = ".gemini_flash_key.txt"
HOME_KEY_FILE = str(Path.home() / ".gemini_personal_api_key.txt")

# জেমিনির বর্তমান ও কার্যকরী মডেল লিস্ট
MODEL_OPTIONS = [
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash-latest",
]

# ==============================================================================
# ২. পেজ কনফিগারেশন ও ডার্ক থিম সিএসএস ডিজাইন
# ==============================================================================
st.set_page_config(
    page_title="Gemini Workspace AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp {
        background: radial-gradient(circle at 55% 40%, #151c33 0%, #0b0d13 55%, #07080c 100%) !important;
        color: #e3e3e3 !important;
        font-family: 'Inter', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #131314 !important;
        border-right: 1px solid #282a2c !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        color: #c4c7c5 !important;
        border: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 8px 14px !important;
        border-radius: 24px !important;
        font-size: 14px !important;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #282a2c !important;
        color: #ffffff !important;
    }
    .main .stButton > button {
        background-color: #1e1f20 !important;
        color: #e3e3e3 !important;
        border: 1px solid #333537 !important;
        border-radius: 20px !important;
        padding: 6px 18px !important;
        font-size: 14px !important;
        transition: all 0.2s ease;
    }
    .main .stButton > button:hover {
        background-color: #2b2d30 !important;
        border-color: #5f6368 !important;
    }
    .welcome-title {
        text-align: center;
        font-size: 2.4rem;
        font-weight: 600;
        background: linear-gradient(90deg, #8ab4f8, #c58af9, #f28b82);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 3vh;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stChatMessage"] {
        background-color: rgba(30, 31, 32, 0.72) !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .section-label {
        font-size: 11px;
        color: #8e918f;
        padding-left: 12px;
        margin-top: 14px;
        margin-bottom: 6px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# ৩. ডাটা স্টোরেজ ও এপিআই কি ম্যানেজমেন্ট
# ==============================================================================
def is_valid_key_string(key_str: str) -> bool:
    if not key_str:
        return False
    return len(key_str.strip()) > 15


def load_workspace():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "chats" in data:
                    data.setdefault(
                        "notebooks",
                        [
                            "পদার্থবিজ্ঞান নোটবুক",
                            "উচ্চতর গণিত নোটবুক",
                            "Spoken English & Language",
                            "Web Dev Notebook",
                        ],
                    )
                    data.setdefault("notebook_notes", {})
                    data.setdefault(
                        "scheduled_tasks",
                        [
                            {
                                "task": "Review daily study & coding goals",
                                "done": False,
                            }
                        ],
                    )
                    data.setdefault(
                        "custom_instruction",
                        "তুমি একজন অত্যন্ত বুদ্ধিমান, বন্ধুসুলভ এবং দক্ষ AI সহকারী ও শিক্ষক। বাংলায় এবং ব্যবহারকারীর কাঙ্ক্ষিত ভাষায় স্পষ্ট, নির্ভুল ও ধাপে ধাপে উত্তর দাও।",
                    )
                    data.setdefault("selected_model", "gemini-1.5-flash")
                    data.setdefault("voice_auto_speak", True)
                    data.setdefault("voice_lang", "bn-BD")
                    data.pop("saved_api_key", None)
                    return data
        except Exception:
            import uuid

            pass

    import uuid

    first_id = str(uuid.uuid4())
    return {
        "chats": {
            first_id: {
                "title": "New chat",
                "mode": "Chat",
                "notebook": None,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "messages": [],
            }
        },
        "notebooks": [
            "পদার্থবিজ্ঞান নোটবুক",
            "উচ্চতর গণিত নোটবুক",
            "Spoken English & Language",
            "Web Dev Notebook",
        ],
        "notebook_notes": {},
        "scheduled_tasks": [
            {"task": "Review daily study & coding goals", "done": False}
        ],
        "custom_instruction": "তুমি একজন অত্যন্ত বুদ্ধিমান, বন্ধুসুলভ এবং দক্ষ AI সহকারী ও শিক্ষক। বাংলায় এবং ব্যবহারকারীর কাঙ্ক্ষিত ভাষায় স্পষ্ট, নির্ভুল ও ধাপে ধাপে উত্তর দাও।",
        "selected_model": "gemini-1.5-flash",
        "voice_auto_speak": True,
        "voice_lang": "bn-BD",
    }


def save_workspace(data):
    try:
        clean_data = dict(data)
        clean_data.pop("saved_api_key", None)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_personal_api_key() -> str:
    # চাইলে সরাসরি আপনার এপিআই কি এখানে কোডের ভেতর বসিয়ে দিতে পারেন (ব্যক্তিগত ব্যবহারের জন্য)
    DIRECT_HARDCODED_KEY = ""  # <-- এখানে আপনার এপিআই কি বসাতে পারেন যদি চান
    if is_valid_key_string(DIRECT_HARDCODED_KEY):
        return DIRECT_HARDCODED_KEY.strip()

    for key_path in (LOCAL_KEY_FILE, HOME_KEY_FILE):
        if os.path.exists(key_path):
            try:
                with open(key_path, "r", encoding="utf-8") as f:
                    saved_key = f.read().strip()
                    if is_valid_key_string(saved_key):
                        return saved_key
            except Exception:
                pass

    try:
        for k_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            if k_name in st.secrets and is_valid_key_string(st.secrets[k_name]):
                return st.secrets[k_name].strip()
    except Exception:
        pass

    for env_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        env_val = os.environ.get(env_name, "")
        if is_valid_key_string(env_val):
            return env_val.strip()

    return ""


def save_personal_api_key(key: str):
    cleaned = key.strip()
    for key_path in (LOCAL_KEY_FILE, HOME_KEY_FILE):
        try:
            with open(key_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
        except Exception:
            pass


if "workspace" not in st.session_state:
    st.session_state.workspace = load_workspace()

ws = st.session_state.workspace

if "api_key" not in st.session_state or not st.session_state.api_key:
    st.session_state.api_key = load_personal_api_key()

import uuid

if (
    "current_chat_id" not in st.session_state
    or st.session_state.current_chat_id not in ws["chats"]
):
    if ws["chats"]:
        st.session_state.current_chat_id = list(ws["chats"].keys())[-1]
    else:
        new_id = str(uuid.uuid4())
        ws["chats"][new_id] = {
            "title": "New chat",
            "mode": "Chat",
            "notebook": None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "messages": [],
        }
        st.session_state.current_chat_id = new_id

if "active_nav" not in st.session_state:
    st.session_state.active_nav = "New chat"

if "search_filter" not in st.session_state:
    st.session_state.search_filter = ""

if "last_processed_audio_hash" not in st.session_state:
    st.session_state.last_processed_audio_hash = ""


def start_new_chat(notebook_name=None, mode=None):
    chosen_mode = mode if mode else "Chat"
    new_id = str(uuid.uuid4())
    ws["chats"][new_id] = {
        "title": f"📓 {notebook_name}" if notebook_name else "New chat",
        "mode": chosen_mode,
        "notebook": notebook_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "messages": [],
    }
    st.session_state.current_chat_id = new_id
    st.session_state.active_nav = "New chat"
    save_workspace(ws)


# ==============================================================================
# ৪. জেমিনি ইঞ্জিন (অটো-ফলব্যাক সহ)
# ==============================================================================
def run_flash_engine(prompt_parts):
    active_key = st.session_state.api_key or load_personal_api_key()
    if not is_valid_key_string(active_key):
        raise ValueError(
            "আপনার ব্যক্তিগত Gemini API Key পাওয়া যায়নি। সাইডবারে 🔑 বাটনে ক্লিক করে কি (Key) সেভ করুন।"
        )

    genai.configure(api_key=active_key)
    preferred_model = ws.get("selected_model", "gemini-1.5-flash")
    candidate_models = [preferred_model] + [
        m for m in MODEL_OPTIONS if m != preferred_model
    ]
    last_err = None

    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt_parts)
            if response and hasattr(response, "text") and response.text:
                return response.text
        except Exception as err:
            last_err = err
            continue

    raise RuntimeError(f"Gemini API Error: {last_err}")


# ==============================================================================
# ৫. ব্রাউজার ভয়েস স্পিকার (TTS)
# ==============================================================================
def render_voice_speaker(
    text_to_speak: str, lang_code: str = "bn-BD", auto_play: bool = False
):
    if not text_to_speak:
        return
    clean_js_text = (
        text_to_speak.replace("\\", " ")
        .replace("`", "'")
        .replace("*", "")
        .replace("#", "")
        .replace("\n", " ")
    )
    clean_js_text_json = json.dumps(clean_js_text)
    auto_flag = "true" if auto_play else "false"

    html_code = f"""
    <div style="display:flex; align-items:center; gap:8px; background:#1a1c23; border:1px solid #2e323b; padding:6px 12px; border-radius:20px; width:fit-content; font-family:sans-serif;">
        <button onclick="speakNow()" style="background:#8ab4f8; color:#0b0d13; border:none; border-radius:14px; padding:4px 12px; cursor:pointer; font-weight:600; font-size:12px;">
            🔊 শুনুন (Speak)
        </button>
        <button onclick="stopSpeak()" style="background:#3c4043; color:#e3e3e3; border:none; border-radius:14px; padding:4px 10px; cursor:pointer; font-size:12px;">
            ⏹️ থামান
        </button>
        <span id="tts_status" style="color:#9aa0a6; font-size:11px;">প্রস্তুত</span>
    </div>
    <script>
        const textData = {clean_js_text_json};
        const targetLang = "{lang_code}";
        const shouldAutoPlay = {auto_flag};

        function speakNow() {{
            if (!('speechSynthesis' in window)) return;
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance(textData);
            utter.lang = targetLang;
            utter.rate = 1.0;
            window.speechSynthesis.speak(utter);
        }}
        function stopSpeak() {{
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        }}
        if (shouldAutoPlay) {{ setTimeout(speakNow, 350); }}
    </script>
    """
    components.html(html_code, height=48)


# ==============================================================================
# ৬. সাইডবার নেভিগেশন
# ==============================================================================
with st.sidebar:
    st.markdown("### ✨ Gemini Workspace")
    if st.button("📝 New chat", use_container_width=True):
        start_new_chat()
        st.rerun()

    if st.button("🎙️ Live Voice & Tutor", use_container_width=True):
        st.session_state.active_nav = "VoiceTutor"
        st.rerun()

    if st.button("🗂️ Library", use_container_width=True):
        st.session_state.active_nav = "Library"
        st.rerun()

    if st.button("🖼️ Images & Vision", use_container_width=True):
        st.session_state.active_nav = "Images"
        st.rerun()

    if st.button("🕒 Scheduled Tasks", use_container_width=True):
        st.session_state.active_nav = "Scheduled"
        st.rerun()

    if st.button("⚙️ Customize & Settings", use_container_width=True):
        st.session_state.active_nav = "Customize"
        st.rerun()

    st.markdown('<div class="section-label">Notebooks</div>', unsafe_allow_html=True)
    for nb in ws["notebooks"]:
        if st.button(f"📓 {nb}", key=f"nb_{nb}", use_container_width=True):
            start_new_chat(notebook_name=nb)
            st.rerun()

    st.markdown("---")
    with st.popover("🔑 API Key Vault"):
        new_key = st.text_input(
            "Gemini API Key:", value=st.session_state.api_key, type="password"
        )
        if st.button("💾 Save Key"):
            st.session_state.api_key = new_key.strip()
            save_personal_api_key(new_key.strip())
            st.success("Saved!")
            st.rerun()


# ==============================================================================
# ৭. মেসেজ প্রসেসিং ফাংশন
# ==============================================================================
current_chat = ws["chats"][st.session_state.current_chat_id]


def process_user_submission(
    display_msg: str, prompt_text: str, image_obj=None, audio_bytes=None
):
    if not is_valid_key_string(st.session_state.api_key):
        st.error(
            "⚠️ অনুগ্রহ করে সাইডবারের 🔑 এপিআই কি ভল্ট থেকে আপনার জেমিনি এপিআই কি সেট করুন।"
        )
        return None

    if len(current_chat["messages"]) == 0:
        current_chat["title"] = display_msg[:30] if display_msg else "AI Chat"

    current_chat["messages"].append({"role": "user", "content": display_msg})

    history_context = "\n".join(
        [
            f"{'User' if m['role'] == 'user' else 'Gemini'}: {m['content']}"
            for m in current_chat["messages"][-10:-1]
        ]
    )

    full_prompt = f"{ws['custom_instruction']}\n{history_context}\n প্রশ্ন: {prompt_text}"

    payload = [full_prompt]
    if image_obj is not None:
        payload.append(image_obj)
    if audio_bytes is not None:
        payload.append({"mime_type": "audio/wav", "data": audio_bytes})

    reply = run_flash_engine(payload)
    current_chat["messages"].append({"role": "assistant", "content": reply})
    save_workspace(ws)
    return reply


# ==============================================================================
# ৮. নেভিগেশন পেজ রাউটিং
# ==============================================================================
if st.session_state.active_nav == "VoiceTutor":
    st.subheader("🎙️ Live Voice & Language Tutor")
    tutor_mic = st.audio_input("কথা বলতে এখানে ক্লিক করুন:")
    if tutor_mic is not None:
        audio_data = tutor_mic.read()
        audio_hash = hashlib.md5(audio_data).hexdigest()
        if audio_hash != st.session_state.last_processed_audio_hash:
            st.session_state.last_processed_audio_hash = audio_hash
            with st.spinner("শোনা হচ্ছে..."):
                try:
                    process_user_submission(
                        "🎤 *[ভয়েস মেসেজ]*",
                        "আমার কথা শুনে প্রাসঙ্গিক উত্তর ও উচ্চারণ ঠিক করে দাও।",
                        audio_bytes=audio_data,
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

    for m in current_chat["messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    if current_chat["messages"] and current_chat["messages"][-1]["role"] == "assistant":
        render_voice_speaker(current_chat["messages"][-1]["content"])
    st.stop()

elif st.session_state.active_nav == "Customize":
    st.subheader("⚙️ Customize & Settings")
    ws["selected_model"] = st.selectbox(
        "Select AI Model:",
        MODEL_OPTIONS,
        index=MODEL_OPTIONS.index(ws.get("selected_model", "gemini-1.5-flash"))
        if ws.get("selected_model") in MODEL_OPTIONS
        else 0,
    )
    ws["custom_instruction"] = st.text_area(
        "Custom Instructions / System Prompt:", value=ws["custom_instruction"]
    )
    if st.button("Save Settings"):
        save_workspace(ws)
        st.success("Settings saved successfully!")
    st.stop()

elif st.session_state.active_nav == "Library":
    st.subheader("🗂️ Library & Chat History")
    for cid, cdata in ws["chats"].items():
        if st.button(f"📄 {cdata['title']} ({cid[:6]})", key=f"lib_{cid}"):
            st.session_state.current_chat_id = cid
            st.session_state.active_nav = "New chat"
            st.rerun()
    st.stop()

# --- ডিফল্ট চ্যাট স্ক্রিন (New chat) ---
st.markdown(
    f'<h1 class="welcome-title">Hello, Shakil</h1>', unsafe_allow_html=True
)

for m in current_chat["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_input = st.chat_input("Ask Gemini in Bangla or English, or use mic...")
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.spinner("Gemini ভাবছে..."):
        try:
            process_user_submission(user_input, user_input)
            st.rerun()
        except Exception as e:
            st.error(f"ত্রুটি: {e}")
