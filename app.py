import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image
import json
import os
import uuid
import hashlib
from pathlib import Path
from datetime import datetime

# ==============================================================================
# ১. ব্যক্তিগত ফাইল ও মডেল কনফিগারেশন (কোডের ভেতর কোনো API Key রাখা হয়নি)
# ==============================================================================
DATA_FILE = "gemini_workspace_data.json"
LOCAL_KEY_FILE = ".gemini_flash_key.txt"
HOME_KEY_FILE = str(Path.home() / ".gemini_personal_api_key.txt")

MODEL_OPTIONS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash-latest",
]

# ==============================================================================
# ২. পেজ কনফিগারেশন ও ডার্ক থিম সিএসএস ডিজাইন (Gemini UI Inspired)
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
    .welcome-sub {
        text-align: center;
        font-size: 1rem;
        color: #9aa0a6;
        margin-bottom: 1.5rem;
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
    .badge-pill {
        display: inline-block;
        background: rgba(138, 180, 248, 0.14);
        color: #8ab4f8;
        border: 1px solid rgba(138, 180, 248, 0.3);
        padding: 3px 12px;
        border-radius: 999px;
        font-size: 12px;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #1e1f20 !important;
        color: #e3e3e3 !important;
        border: 1px solid #3c4043 !important;
        border-radius: 12px !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# ৩. ডাটা স্টোরেজ, ব্যক্তিগত API Key ভল্ট এবং সেশন স্টেট ম্যানেজমেন্ট
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
                        [{"task": "Review daily ML research papers at 8 PM", "done": False}],
                    )
                    data.setdefault(
                        "custom_instruction",
                        "তুমি একজন অত্যন্ত বুদ্ধিমান, বন্ধুসুলভ এবং দক্ষ AI সহকারী ও শিক্ষক। বাংলায় এবং ব্যবহারকারীর কাঙ্ক্ষিত ভাষায় স্পষ্ট, নির্ভুল ও ধাপে ধাপে উত্তর দাও।",
                    )
                    data.setdefault("selected_model", "gemini-2.5-flash")
                    data.setdefault("voice_auto_speak", True)
                    data.setdefault("voice_lang", "bn-BD")
                    # নিরাপত্তার জন্য ওয়ার্কস্পেস ডাটা ফাইলে কখনোই API Key রাখা হবে না
                    data.pop("saved_api_key", None)
                    return data
        except Exception:
            pass

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
        "scheduled_tasks": [{"task": "Review daily ML research papers at 8 PM", "done": False}],
        "custom_instruction": "তুমি একজন অত্যন্ত বুদ্ধিমান, বন্ধুসুলভ এবং দক্ষ AI সহকারী ও শিক্ষক। বাংলায় এবং ব্যবহারকারীর কাঙ্ক্ষিত ভাষায় স্পষ্ট, নির্ভুল ও ধাপে ধাপে উত্তর দাও।",
        "selected_model": "gemini-2.5-flash",
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
    """ব্যবহারকারীর ব্যক্তিগত ফাইল, Streamlit secrets অথবা Environment থেকে API Key লোড করে (কোডে কোনো Key থাকে না)।"""
    # ১. ইউজারের হোম ডিরেক্টরি ও লোকাল প্রাইভেট ফাইল চেক করা
    for key_path in (LOCAL_KEY_FILE, HOME_KEY_FILE):
        if os.path.exists(key_path):
            try:
                with open(key_path, "r", encoding="utf-8") as f:
                    saved_key = f.read().strip()
                    if is_valid_key_string(saved_key):
                        return saved_key
            except Exception:
                pass

    # ২. Streamlit secrets চেক করা (.streamlit/secrets.toml)
    try:
        for k_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            if k_name in st.secrets and is_valid_key_string(st.secrets[k_name]):
                return st.secrets[k_name].strip()
    except Exception:
        pass

    # ৩. সিস্টেম Environment Variable চেক করা
    for env_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        env_val = os.environ.get(env_name, "")
        if is_valid_key_string(env_val):
            return env_val.strip()

    return ""


def save_personal_api_key(key: str):
    """ব্যবহারকারীর API Key শুধুমাত্র ব্যক্তিগত গোপন ফাইলে সংরক্ষণ করে (মূল কোডে বা চ্যাট ডাটায় নয়)।"""
    cleaned = key.strip()
    for key_path in (LOCAL_KEY_FILE, HOME_KEY_FILE):
        try:
            with open(key_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
        except Exception:
            pass


def delete_personal_api_key():
    """ব্যক্তিগতভাবে সংরক্ষিত API Key মুছে ফেলার ফাংশন।"""
    for key_path in (LOCAL_KEY_FILE, HOME_KEY_FILE):
        if os.path.exists(key_path):
            try:
                os.remove(key_path)
            except Exception:
                pass


# সেশন স্টেট ইনিশিয়ালাইজেশন
if "workspace" not in st.session_state:
    st.session_state.workspace = load_workspace()

ws = st.session_state.workspace

if "api_key" not in st.session_state or not st.session_state.api_key:
    st.session_state.api_key = load_personal_api_key()

if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in ws["chats"]:
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

if "interaction_mode" not in st.session_state:
    current_c = ws["chats"].get(st.session_state.current_chat_id, {})
    st.session_state.interaction_mode = current_c.get("mode", "Chat")

if "selected_model" not in st.session_state:
    st.session_state.selected_model = ws.get("selected_model", "gemini-2.5-flash")

if "search_filter" not in st.session_state:
    st.session_state.search_filter = ""

if "last_processed_audio_hash" not in st.session_state:
    st.session_state.last_processed_audio_hash = ""

if "last_tts_text" not in st.session_state:
    st.session_state.last_tts_text = ""


def start_new_chat(notebook_name=None, mode=None):
    chosen_mode = mode if mode else st.session_state.interaction_mode
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


def open_or_create_notebook_chat(notebook_name: str):
    for cid in reversed(list(ws["chats"].keys())):
        if ws["chats"][cid].get("notebook") == notebook_name:
            st.session_state.current_chat_id = cid
            st.session_state.active_nav = "New chat"
            return
    start_new_chat(notebook_name=notebook_name)


# ==============================================================================
# ৪. জেমিনি ফ্ল্যাশ ও মাল্টিমোডাল ইঞ্জিন (অটো-ফলব্যাক সহ)
# ==============================================================================
def run_flash_engine(prompt_parts):
    active_key = st.session_state.api_key or load_personal_api_key()
    if not is_valid_key_string(active_key):
        raise ValueError(
            "আপনার ব্যক্তিগত Gemini API Key এখনো সেভ করা হয়নি। বাম পাশের সাইডবারে 🔑 বাটনে অথবা ⚙️ Customize & Settings-এ গিয়ে আপনার ব্যক্তিগত API Key সেভ করুন।"
        )

    genai.configure(api_key=active_key)
    preferred_model = st.session_state.get("selected_model", "gemini-2.5-flash")

    candidate_models = [preferred_model] + [m for m in MODEL_OPTIONS if m != preferred_model]
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
# ৫. ব্রাউজার-ভিত্তিক ভয়েস আউটপুট (Text-to-Speech) প্লেয়ার
# ==============================================================================
def render_voice_speaker(text_to_speak: str, lang_code: str = "bn-BD", auto_play: bool = False):
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
            if (!('speechSynthesis' in window)) {{
                document.getElementById('tts_status').innerText = 'ব্রাউজার সাপোর্ট করছে না';
                return;
            }}
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance(textData);
            utter.lang = targetLang;
            utter.rate = 1.0;

            const voices = window.speechSynthesis.getVoices();
            const matched = voices.find(v => v.lang.toLowerCase().includes(targetLang.split('-')[0].toLowerCase()));
            if (matched) utter.voice = matched;

            utter.onstart = () => {{ document.getElementById('tts_status').innerText = '🔊 বলছে...'; }};
            utter.onend = () => {{ document.getElementById('tts_status').innerText = 'সম্পন্ন'; }};
            utter.onerror = () => {{ document.getElementById('tts_status').innerText = 'প্রস্তুত'; }};
            window.speechSynthesis.speak(utter);
        }}

        function stopSpeak() {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                document.getElementById('tts_status').innerText = 'থামানো হয়েছে';
            }}
        }}

        if (shouldAutoPlay) {{
            setTimeout(speakNow, 350);
        }}
    </script>
    """
    components.html(html_code, height=48)


# ==============================================================================
# ৬. সাইডবার নেভিগেশন ও ওয়ার্কস্পেস কন্ট্রোল
# ==============================================================================
with st.sidebar:
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("### ✨ Gemini Workspace")
    with c2:
        with st.popover("🔍"):
            st.session_state.search_filter = st.text_input(
                "চ্যাট খুঁজুন...", value=st.session_state.search_filter
            )

    if st.button("📝 New chat", use_container_width=True):
        start_new_chat()
        st.rerun()

    if st.button("🎙️ Live Voice & Language Tutor", use_container_width=True):
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

    if st.button("••• More Tools", use_container_width=True):
        st.session_state.active_nav = "More"
        st.rerun()

    # নোটবুক সেকশন
    st.markdown('<div class="section-label">Notebooks</div>', unsafe_allow_html=True)
    with st.popover("➕ New notebook", use_container_width=True):
        nb_name = st.text_input("নতুন নোটবুকের নাম:")
        if st.button("তৈরি করুন", key="create_nb_btn") and nb_name.strip():
            clean_nb = nb_name.strip()
            if clean_nb not in ws["notebooks"]:
                ws["notebooks"].append(clean_nb)
                save_workspace(ws)
            start_new_chat(notebook_name=clean_nb)
            st.rerun()

    for nb in ws["notebooks"]:
        if st.button(f"📓 {nb}", key=f"nb_{nb}", use_container_width=True):
            open_or_create_notebook_chat(nb)
            st.rerun()

    # রিসেন্ট চ্যাট হিস্ট্রি
    st.markdown('<div class="section-label">Recent Chats</div>', unsafe_allow_html=True)
    chat_ids = list(ws["chats"].keys())[::-1]
    for cid in chat_ids:
        chat_item = ws["chats"][cid]
        if (
            st.session_state.search_filter
            and st.session_state.search_filter.lower() not in chat_item["title"].lower()
        ):
            continue
        col_title, col_del = st.columns([5, 1])
        with col_title:
            dot = (
                "🔵 "
                if (cid == st.session_state.current_chat_id and st.session_state.active_nav == "New chat")
                else ""
            )
            if st.button(
                f"{dot}{chat_item['title'][:22]}",
                key=f"hist_{cid}",
                use_container_width=True,
            ):
                st.session_state.current_chat_id = cid
                st.session_state.active_nav = "New chat"
                st.rerun()
        with col_del:
            if st.button("✖", key=f"del_{cid}"):
                del ws["chats"][cid]
                if not ws["chats"]:
                    start_new_chat()
                else:
                    st.session_state.current_chat_id = list(ws["chats"].keys())[-1]
                save_workspace(ws)
                st.rerun()

    st.markdown("---")
    p1, p2 = st.columns([4, 1])
    with p1:
        key_ready = is_valid_key_string(st.session_state.api_key)
        status_dot = "🟢" if key_ready else "🟠"
        status_txt = f"{st.session_state.selected_model} • Ready" if key_ready else "Personal Key Needed"
        st.markdown(
            f"{status_dot} **প্রোফাইল** \n<span style='font-size:11px;color:#8e918f;'>{status_txt}</span>",
            unsafe_allow_html=True,
        )
    with p2:
        with st.popover("🔑"):
            st.markdown("**ব্যক্তিগত API Key ভল্ট**")
            st.caption("আপনার Key কোডে থাকবে না, শুধুমাত্র আপনার ডিভাইসে প্রাইভেট ফাইলে সেভ থাকবে।")
            new_key = st.text_input(
                "Gemini API Key:",
                value=st.session_state.api_key,
                type="password",
                key="sidebar_api_input",
            )
            k_c1, k_c2 = st.columns(2)
            with k_c1:
                if st.button("💾 সেভ", key="save_sidebar_key", use_container_width=True):
                    st.session_state.api_key = new_key.strip()
                    save_personal_api_key(new_key.strip())
                    st.success("সংরক্ষিত!")
                    st.rerun()
            with k_c2:
                if st.button("🗑️ মুছুন", key="clear_sidebar_key", use_container_width=True):
                    st.session_state.api_key = ""
                    delete_personal_api_key()
                    st.rerun()


# ==============================================================================
# ৭. মেসেজ প্রসেসিং হেল্পার ফাংশন (টেক্সট, ইমেজ, পিডিএফ ও ভয়েস)
# ==============================================================================
current_chat = ws["chats"][st.session_state.current_chat_id]


def process_user_submission(
    display_msg: str,
    prompt_text: str,
    image_obj=None,
    audio_bytes=None,
    audio_mime="audio/wav",
    pdf_bytes=None,
    doc_text="",
    extra_system_hint="",
):
    if not is_valid_key_string(st.session_state.api_key):
        st.error(
            "⚠️ অনুগ্রহ করে বাম পাশের সাইডবারে 🔑 বাটনে অথবা নিচের বক্সে আপনার ব্যক্তিগত Gemini API Key একবার সেভ করুন।"
        )
        return None

    if len(current_chat["messages"]) == 0:
        clean_title = (
            display_msg.replace("🎤", "")
            .replace("*[ভয়েস মেসেজ]*", "")
            .replace("📎", "")
            .strip()[:30]
        )
        current_chat["title"] = clean_title if clean_title else "ভয়েস ও এআই আলোচনা"

    current_chat["messages"].append({"role": "user", "content": display_msg})

    history_context = "\n".join(
        [
            f"{'User' if m['role'] == 'user' else 'Gemini'}: {m['content']}"
            for m in current_chat["messages"][-12:-1]
        ]
    )

    mode_instruction = ""
    if current_chat.get("mode") == "Task":
        mode_instruction = (
            "তুমি এখন 'Task Solver Mode'-এ আছো। যেকোনো সমস্যার একদম সুনির্দিষ্ট, ধাপে ধাপে (Step-by-step), কার্যকরী ও প্র্যাকটিক্যাল সমাধান দেবে।\n"
        )
    elif current_chat.get("mode") == "Voice":
        mode_instruction = (
            "তুমি এখন 'Voice & Language Coach Mode'-এ আছো। উত্তর সংক্ষিপ্ত, কথোপকথনের মতো সাবলীল এবং উচ্চারণ ও ভাষা শেখার উপযোগী রাখবে।\n"
        )

    nb_name = current_chat.get("notebook")
    nb_context = ""
    if nb_name:
        saved_note = ws.get("notebook_notes", {}).get(nb_name, "")
        nb_context = f"বর্তমান নোটবুক: {nb_name}\n"
        if saved_note:
            nb_context += f"নোটবুকের সংরক্ষিত তথ্য:\n{saved_note}\n"

    full_prompt = f"{ws['custom_instruction']}\n{mode_instruction}{extra_system_hint}\n"
    if nb_context:
        full_prompt += f"\n{nb_context}\n"
    if history_context:
        full_prompt += f"\nপূর্ববর্তী কথোপকথন:\n{history_context}\n---\n"
    if doc_text:
        full_prompt += f"\nসংযুক্ত ফাইলের বিষয়বস্তু:\n{doc_text[:15000]}\n---\n"
    full_prompt += f"\nব্যবহারকারীর ইনপুট/প্রশ্ন: {prompt_text}"

    payload = [full_prompt]
    if image_obj is not None:
        payload.append(image_obj)
    if pdf_bytes is not None:
        payload.append({"mime_type": "application/pdf", "data": pdf_bytes})
    if audio_bytes is not None:
        payload.append({"mime_type": audio_mime, "data": audio_bytes})

    reply = run_flash_engine(payload)
    current_chat["messages"].append({"role": "assistant", "content": reply})
    st.session_state.last_tts_text = reply
    save_workspace(ws)
    return reply


# ==============================================================================
# ৮. ব্যক্তিগত API Key কুইক সেটআপ বক্স (যদি এখনো সেভ করা না থাকে)
# ==============================================================================
if not is_valid_key_string(st.session_state.api_key):
    with st.container():
        st.info(
            "🔐 **ব্যক্তিগত API Key সেটআপ:** নিরাপত্তার জন্য কোডের ভেতরে কোনো API Key রাখা হয়নি। নিচে আপনার Gemini API Key দিয়ে একবার **'ব্যক্তিগতভাবে সেভ করুন'** বাটনে ক্লিক করলে এটি আপনার ডিভাইসে গোপনে সেভ থাকবে এবং পরবর্তীতে অ্যাপ চালু করলে স্বয়ংক্রিয়ভাবে কাজ করবে।"
        )
        pk_col1, pk_col2 = st.columns([3.5, 1.2])
        with pk_col1:
            quick_key = st.text_input(
                "আপনার ব্যক্তিগত Gemini API Key লিখুন:",
                type="password",
                placeholder="AIzaSy...",
                key="welcome_personal_key",
                label_visibility="collapsed",
            )
        with pk_col2:
            if st.button("🔐 ব্যক্তিগতভাবে সেভ করুন", use_container_width=True):
                if is_valid_key_string(quick_key):
                    st.session_state.api_key = quick_key.strip()
                    save_personal_api_key(quick_key.strip())
                    st.success("✅ আপনার API Key ব্যক্তিগত ফাইলে সুরক্ষিতভাবে সেভ হয়েছে!")
                    st.rerun()
                else:
                    st.error("অনুগ্রহ করে একটি সঠিক Gemini API Key দিন।")


# ==============================================================================
# ৯. বিভিন্ন ট্যাব ও বিশেষায়িত ফিচার ভিউ
# ==============================================================================
# --- ট্যাব ১: Live Voice & Language Tutor ---
if st.session_state.active_nav == "VoiceTutor":
    st.subheader("🎙️ রিয়েল-টাইম ভয়েস ও ভাষা শিক্ষা টিউটর (Voice & Language Coach)")
    st.caption(
        "মাইক্রোফোনে সরাসরি কথা বলুন! জেমিনি আপনার কথা শুনে উত্তর দেবে, উচ্চারণ ও ব্যাকরণ সংশোধন করবে এবং নিজে ভয়েসে কথা বলে শোনাবে।"
    )

    vc1, vc2, vc3 = st.columns([1.5, 1.5, 1])
    with vc1:
        practice_topic = st.selectbox(
            "🎯 অনুশীলনের বিষয় বা ভাষা নির্বাচন করুন:",
            [
                "Spoken English Practice (ইংরেজি কথোপকথন ও ফ্লুয়েন্সি)",
                "যেকোনো বিষয় বাংলায় সহজভাবে শেখা (Bangla Voice Tutor)",
                "IELTS Speaking Mock Test & Feedback",
                "Arabic / Hindi / Japanese / Spanish Language Practice",
                "Job Interview & Presentation Practice",
            ],
        )
    with vc2:
        voice_lang_map = {
            "বাংলা + English (bn-BD)": "bn-BD",
            "English US (en-US)": "en-US",
            "English UK (en-GB)": "en-GB",
            "Hindi (hi-IN)": "hi-IN",
            "Arabic (ar-SA)": "ar-SA",
            "Japanese (ja-JP)": "ja-JP",
            "Spanish (es-ES)": "es-ES",
        }
        chosen_lang_label = st.selectbox("🔊 এআই ভয়েস আউটপুট ভাষা:", list(voice_lang_map.keys()))
        ws["voice_lang"] = voice_lang_map[chosen_lang_label]
    with vc3:
        ws["voice_auto_speak"] = st.toggle(
            "উত্তর স্বয়ংক্রিয়ভাবে পড়ে শোনাবে", value=ws.get("voice_auto_speak", True)
        )

    st.markdown("---")
    tutor_mic = st.audio_input(
        "🎤 এখানে চাপ দিয়ে কথা বলুন (রেকর্ডিং শেষ করলেই স্বয়ংক্রিয়ভাবে উত্তর আসবে):",
        key="tutor_live_mic",
    )

    if tutor_mic is not None:
        audio_data = tutor_mic.read()
        audio_hash = hashlib.md5(audio_data).hexdigest()
        if audio_hash != st.session_state.last_processed_audio_hash:
            st.session_state.last_processed_audio_hash = audio_hash
            with st.spinner("🎧 আপনার কথা শোনা হচ্ছে এবং উত্তর তৈরি হচ্ছে..."):
                try:
                    tutor_prompt = (
                        f"ব্যবহারকারী ভয়েস অডিও পাঠিয়েছেন। অনুশীলনের মোড: {practice_topic}।\n"
                        "১. প্রথমে ব্র্যাকেটে [শোনা গেছে: ...] লিখে ব্যবহারকারী কী বলেছেন তা সংক্ষেপে উল্লেখ করো।\n"
                        "২. এরপর তার কথার প্রাসঙ্গিক, স্বাভাবিক ও বন্ধুসুলভ উত্তর দাও।\n"
                        "৩. যদি তিনি ভাষা চর্চা করেন, তবে তার বাক্যে কোনো ব্যাকরণ বা উচ্চারণগত উন্নতির সুযোগ থাকলে নিচে সংক্ষেপে সুন্দরভাবে শিখিয়ে দাও এবং পরবর্তী একটি প্রশ্ন করো যাতে কথোপকথন চলতে থাকে।"
                    )
                    process_user_submission(
                        display_msg="🎤 *[ভয়েস কথোপকথন]*",
                        prompt_text=tutor_prompt,
                        audio_bytes=audio_data,
                        audio_mime=tutor_mic.type or "audio/wav",
                    )
                except Exception as e:
                    st.error(f"ত্রুটি: {e}")

    if current_chat["messages"]:
        for m in current_chat["messages"][-6:]:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
        last_msg = current_chat["messages"][-1]
        if last_msg["role"] == "assistant":
            render_voice_speaker(
                last_msg["content"],
                lang_code=ws.get("voice_lang", "bn-BD"),
                auto_play=ws.get("voice_auto_speak", True),
            )
    st.stop()

# --- ট্যাব ২: Library ---
elif st.session_state.active_nav == "Library":
    st.subheader("🗂️ Workspace Library")
    st.caption("আপনার সকল সংরক্ষিত চ্যাট, নোটবুক এবং কথোপকথনের তালিকা।")
    for cid, cdata in list(ws["chats"].items())[::-1]:
        with st.expander(f"📄 {cdata['title']} ({cdata.get('created_at', '')})"):
            st.write(
                f"**মোড:** `{cdata.get('mode', 'Chat')}` | **নোটবুক:** `{cdata.get('notebook') or 'সাধারণ'}` | **মেসেজ সংখ্যা:** `{len(cdata.get('messages', []))}`"
            )
            c_open, c_export = st.columns([1, 1])
            with c_open:
                if st.button("📂 এই চ্যাটটি ওপেন করুন", key=f"lib_{cid}"):
                    st.session_state.current_chat_id = cid
                    st.session_state.active_nav = "New chat"
                    st.rerun()
            with c_export:
                chat_txt = "\n\n".join(
                    [f"{m['role'].upper()}:\n{m['content']}" for m in cdata.get("messages", [])]
                )
                st.download_button(
                    "⬇️ ডাউনলোড (.txt)",
                    data=chat_txt or "Empty chat",
                    file_name=f"chat_{cid[:8]}.txt",
                    mime="text/plain",
                    key=f"dl_{cid}",
                )
    st.stop()

# --- ট্যাব ৩: Images & Vision ---
elif st.session_state.active_nav == "Images":
    st.subheader("🖼️ Images, Diagrams & Handwriting Analysis")
    img_file = st.file_uploader(
        "ছবি, ডায়াগ্রাম বা খাতার পাতা আপলোড করুন:", type=["png", "jpg", "jpeg", "webp"]
    )
    if img_file:
        img_obj = Image.open(img_file)
        st.image(img_obj, width=420)
        img_q = st.text_input(
            "ছবি সম্পর্কিত নির্দেশ বা প্রশ্ন লিখুন:",
            value="এই ছবি বা খাতার লেখাটি নিখুঁতভাবে বিশ্লেষণ করে বিস্তারিত বুঝিয়ে দাও।",
        )
        col_an1, col_an2 = st.columns([1, 1])
        with col_an1:
            if st.button("🔍 বিশ্লেষণ শুরু করুন", use_container_width=True):
                with st.spinner("এআই ছবি বিশ্লেষণ করছে..."):
                    try:
                        ans = process_user_submission(
                            display_msg=f"🖼️ *[ছবি বিশ্লেষণ: {img_file.name}]* — {img_q}",
                            prompt_text=img_q,
                            image_obj=img_obj,
                        )
                        if ans:
                            st.markdown("### ✨ বিশ্লেষণের ফলাফল:")
                            st.markdown(ans)
                            render_voice_speaker(
                                ans, lang_code=ws.get("voice_lang", "bn-BD"), auto_play=False
                            )
                    except Exception as e:
                        st.error(f"ত্রুটি: {e}")
        with col_an2:
            if st.button("💬 চ্যাট স্ক্রিনে নিয়ে যান", use_container_width=True):
                st.session_state["pending_img"] = img_obj
                st.session_state["pending_img_name"] = img_file.name
                st.session_state.active_nav = "New chat"
                st.rerun()
    st.stop()

# --- ট্যাব ৪: Scheduled Tasks ---
elif st.session_state.active_nav == "Scheduled":
    st.subheader("🕒 Scheduled Tasks & AI Action Runner")
    col_t1, col_t2 = st.columns([4, 1])
    with col_t1:
        new_task = st.text_input("নতুন টাস্ক, রুটিন বা রিমাইন্ডার লিখুন:")
    with col_t2:
        st.write("")
        if st.button("➕ যোগ করুন", use_container_width=True) and new_task.strip():
            ws["scheduled_tasks"].append({"task": new_task.strip(), "done": False})
            save_workspace(ws)
            st.rerun()

    for idx, t in enumerate(list(ws["scheduled_tasks"])):
        tc1, tc2, tc3, tc4 = st.columns([0.5, 4, 1.5, 0.8])
        with tc1:
            done_state = st.checkbox("", value=t.get("done", False), key=f"chk_{idx}")
            if done_state != t.get("done", False):
                ws["scheduled_tasks"][idx]["done"] = done_state
                save_workspace(ws)
                st.rerun()
        with tc2:
            task_title = f"~~{t['task']}~~" if t.get("done") else f"**{t['task']}**"
            st.markdown(f"{idx + 1}. {task_title}")
        with tc3:
            if st.button("⚡ AI দিয়ে সমাধান", key=f"run_t_{idx}"):
                st.session_state.active_nav = "New chat"
                with st.spinner("টাস্কটি সম্পন্ন করা হচ্ছে..."):
                    process_user_submission(
                        display_msg=f"🕒 [Scheduled Task] {t['task']}",
                        prompt_text=f"আমার নির্ধারিত টাস্ক হলো: '{t['task']}'। এই টাস্কটি সম্পন্ন করার জন্য বিস্তারিত গাইড, সারসংক্ষেপ বা সমাধান তৈরি করে দাও।",
                    )
                st.rerun()
        with tc4:
            if st.button("🗑️", key=f"del_t_{idx}"):
                ws["scheduled_tasks"].pop(idx)
                save_workspace(ws)
                st.rerun()
    st.stop()

# --- ট্যাব ৫: Customize & Settings ---
elif st.session_state.active_nav == "Customize":
    st.subheader("⚙️ Customize Settings, Personal API Key & AI Persona")
    custom_inst = st.text_area(
        "সিস্টেম ইনস্ট্রাকশন (AI Persona):", value=ws["custom_instruction"], height=120
    )
    api_k = st.text_input(
        "আপনার ব্যক্তিগত Gemini API Key (কোডের বাইরে আপনার প্রাইভেট ফাইলে সংরক্ষিত থাকবে):",
        value=st.session_state.api_key,
        type="password",
    )

    curr_model = st.session_state.get("selected_model", "gemini-2.5-flash")
    m_idx = MODEL_OPTIONS.index(curr_model) if curr_model in MODEL_OPTIONS else 0
    model_choice = st.selectbox("ডিফল্ট জেমিনি মডেল নির্বাচন করুন:", MODEL_OPTIONS, index=m_idx)

    auto_spk = st.checkbox(
        "ভয়েস ইনপুটের উত্তর স্বয়ংক্রিয়ভাবে ভয়েসে পড়ে শোনাবে (Auto Voice Response)",
        value=ws.get("voice_auto_speak", True),
    )

    s_col1, s_col2 = st.columns([2, 1])
    with s_col1:
        if st.button("💾 পরিবর্তনগুলো ও ব্যক্তিগত API Key সেভ করুন", use_container_width=True):
            ws["custom_instruction"] = custom_inst
            ws["selected_model"] = model_choice
            ws["voice_auto_speak"] = auto_spk
            st.session_state.api_key = api_k.strip()
            st.session_state.selected_model = model_choice
            save_personal_api_key(api_k.strip())
            save_workspace(ws)
            st.success("✅ সকল সেটিংস এবং আপনার ব্যক্তিগত API Key সুরক্ষিতভাবে সংরক্ষিত হয়েছে!")
    with s_col2:
        if st.button("🗑️ সংরক্ষিত API Key মুছে ফেলুন", use_container_width=True):
            st.session_state.api_key = ""
            delete_personal_api_key()
            st.warning("সংরক্ষিত API Key মুছে ফেলা হয়েছে।")
            st.rerun()
    st.stop()

# --- ট্যাব ৬: More Tools ---
elif st.session_state.active_nav == "More":
    st.subheader("••• Advanced Workspace Tools")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("#### 📥 ওয়ার্কস্পেস ব্যাকআপ (API Key ব্যতীত নিরাপদ ব্যাকআপ)")
        clean_backup = dict(ws)
        clean_backup.pop("saved_api_key", None)
        st.download_button(
            "⬇️ সম্পূর্ণ ডাটা ব্যাকআপ ডাউনলোড (.json)",
            data=json.dumps(clean_backup, ensure_ascii=False, indent=2),
            file_name="gemini_workspace_backup.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_m2:
        st.markdown("#### 🗑️ হিস্ট্রি রিসেট")
        if st.button("⚠️ সকল চ্যাট হিস্ট্রি মুছে ফেলুন", use_container_width=True):
            ws["chats"] = {}
            start_new_chat()
            st.success("সকল চ্যাট হিস্ট্রি রিসেট করা হয়েছে!")
            st.rerun()
    st.stop()


# ==============================================================================
# ১০. মেইন চ্যাট ইন্টারফেস (সর্বদা সক্রিয় মাল্টিমোডাল টুলবার ও ভয়েস বার সহ)
# ==============================================================================
top_c1, top_c2, top_c3 = st.columns([2.2, 1.8, 1.2])
with top_c1:
    active_nb = current_chat.get("notebook")
    nb_badge = f'<span class="badge-pill">📓 {active_nb}</span>' if active_nb else ""
    mode_badge = f'<span class="badge-pill">⚡ {current_chat.get("mode", "Chat")} Mode</span>'
    model_badge = f'<span class="badge-pill">🤖 {st.session_state.selected_model}</span>'
    st.markdown(f"{nb_badge}{mode_badge}{model_badge}", unsafe_allow_html=True)

with top_c2:
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        if st.button("💬 Chat", use_container_width=True):
            st.session_state.interaction_mode = "Chat"
            current_chat["mode"] = "Chat"
            save_workspace(ws)
            st.rerun()
    with mc2:
        if st.button("⚡ Task", use_container_width=True):
            st.session_state.interaction_mode = "Task"
            current_chat["mode"] = "Task"
            save_workspace(ws)
            st.rerun()
    with mc3:
        if st.button("🎙️ Voice", use_container_width=True):
            st.session_state.interaction_mode = "Voice"
            current_chat["mode"] = "Voice"
            save_workspace(ws)
            st.rerun()

with top_c3:
    if active_nb:
        with st.popover("📝 নোটবুক নোট", use_container_width=True):
            curr_note = ws.get("notebook_notes", {}).get(active_nb, "")
            updated_note = st.text_area(
                f"'{active_nb}'-এর স্থায়ী রেফারেন্স নোট:", value=curr_note, height=130
            )
            if st.button("নোট সেভ করুন"):
                ws.setdefault("notebook_notes", {})[active_nb] = updated_note
                save_workspace(ws)
                st.success("নোট সংরক্ষিত!")

# যদি চ্যাট খালি থাকে তবে ওয়েলকাম স্ক্রিন ও কুইক প্রম্পট দেখাবে
if len(current_chat["messages"]) == 0:
    st.markdown('<div class="welcome-title">Where should we start?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="welcome-sub">যেকোনো প্রশ্ন লিখুন, ফাইল/ছবি যুক্ত করুন অথবা সরাসরি মাইক্রোফোনে কথা বলুন</div>',
        unsafe_allow_html=True,
    )

    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("📖 ক্যালকুলাসের ইন্টিগ্রেশন সহজভাবে বুঝিয়ে দাও", use_container_width=True):
            with st.spinner("উত্তর তৈরি হচ্ছে..."):
                process_user_submission(
                    "📖 ক্যালকুলাসের ইন্টিগ্রেশন সহজভাবে বুঝিয়ে দাও",
                    "ক্যালকুলাসের ইন্টিগ্রেশন (Integration) কী, কেন প্রয়োজন এবং বাস্তব উদাহরণসহ সহজ বাংলায় ধাপে ধাপে বুঝিয়ে দাও।",
                )
            st.rerun()
    with q2:
        if st.button("🗣️ Spoken English ও ভোকাবুলারি অনুশীলন শুরু করো", use_container_width=True):
            with st.spinner("প্রস্তুত হচ্ছে..."):
                process_user_submission(
                    "🗣️ Spoken English ও ভোকাবুলারি অনুশীলন শুরু করো",
                    "আমি তোমার সাথে কথা বলে এবং চ্যাট করে ইংরেজি ভাষা সাবলীলভাবে শিখতে চাই। একজন চমৎকার ভাষা শিক্ষকের মতো আমাকে আজকের প্রথম কথোপকথন শুরু করতে একটি সহজ প্রশ্ন করো এবং নিয়ম বুঝিয়ে দাও।",
                )
            st.rerun()
    with q3:
        if st.button("💡 প্রতিদিনের পড়াশোনার একটি কার্যকরী রুটিন তৈরি করো", use_container_width=True):
            with st.spinner("রুটিন তৈরি হচ্ছে..."):
                process_user_submission(
                    "💡 প্রতিদিনের পড়াশোনার একটি কার্যকরী রুটিন তৈরি করো",
                    "একজন শিক্ষার্থীর জন্য প্রতিদিনের পড়াশোনা, রিভিশন এবং দক্ষতা উন্নয়নের একটি বিজ্ঞানসম্মত ও কার্যকরী সময়সূচি তৈরি করে দাও।",
                )
            st.rerun()
else:
    for idx, msg in enumerate(current_chat["messages"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and idx == len(current_chat["messages"]) - 1:
                auto_play_now = (
                    current_chat.get("mode") == "Voice" and ws.get("voice_auto_speak", True)
                )
                render_voice_speaker(
                    msg["content"],
                    lang_code=ws.get("voice_lang", "bn-BD"),
                    auto_play=auto_play_now,
                )

# ==============================================================================
# ১১. সর্বদা দৃশ্যমান মাল্টিমোডাল অ্যাটটাচমেন্ট ও রিয়েল-টাইম মাইক্রোফোন বার
# ==============================================================================
bar_c1, bar_c2, bar_c3 = st.columns([1.2, 1.2, 3.6])

with bar_c1:
    with st.popover("➕ ফাইল / ছবি যুক্ত করুন", use_container_width=True):
        attached_file = st.file_uploader(
            "ছবি, PDF বা টেক্সট ফাইল দিন",
            type=["png", "jpg", "jpeg", "webp", "txt", "md", "py", "csv", "pdf"],
            key=f"chat_up_{st.session_state.current_chat_id}",
        )
        if attached_file is not None:
            fname = attached_file.name
            if attached_file.type.startswith("image/"):
                st.session_state["pending_img"] = Image.open(attached_file)
                st.session_state["pending_img_name"] = fname
                st.success(f"🖼️ ছবি প্রস্তুত: {fname}")
            elif attached_file.type == "application/pdf" or fname.lower().endswith(".pdf"):
                st.session_state["pending_pdf"] = attached_file.read()
                st.session_state["pending_pdf_name"] = fname
                st.success(f"📕 PDF প্রস্তুত: {fname}")
            else:
                txt_data = attached_file.read().decode("utf-8", errors="ignore")
                st.session_state["pending_txt"] = txt_data
                st.session_state["pending_txt_name"] = fname
                st.success(f"📄 ফাইল প্রস্তুত: {fname}")

with bar_c2:
    with st.popover("🎙️ ভয়েস মেসেজ / কথা বলুন", use_container_width=True):
        st.caption("রেকর্ড শেষ করলেই স্বয়ংক্রিয়ভাবে জেমিনি উত্তর দেবে:")
        chat_voice = st.audio_input("মাইক্রোফোন:", key=f"chat_mic_{st.session_state.current_chat_id}")
        if chat_voice is not None:
            v_bytes = chat_voice.read()
            v_hash = hashlib.md5(v_bytes).hexdigest()
            if v_hash != st.session_state.last_processed_audio_hash:
                st.session_state.last_processed_audio_hash = v_hash
                current_chat["mode"] = "Voice"
                with st.spinner("🎧 ভয়েস প্রসেস হচ্ছে..."):
                    try:
                        process_user_submission(
                            display_msg="🎤 *[ভয়েস প্রশ্ন]*",
                            prompt_text=(
                                "ব্যবহারকারী এই ভয়েস অডিওটি পাঠিয়েছেন। প্রথমে [শোনা গেছে: ...] লিখে তিনি কী বলেছেন তা উল্লেখ করো, তারপর তার কথার সুনির্দিষ্ট ও সাবলীল উত্তর দাও।"
                            ),
                            audio_bytes=v_bytes,
                            audio_mime=chat_voice.type or "audio/wav",
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"ভয়েস প্রসেসিং ত্রুটি: {e}")

with bar_c3:
    pending_badges = []
    if "pending_img" in st.session_state:
        pending_badges.append(f"🖼️ {st.session_state.get('pending_img_name', 'Image')}")
    if "pending_pdf" in st.session_state:
        pending_badges.append(f"📕 {st.session_state.get('pending_pdf_name', 'PDF')}")
    if "pending_txt" in st.session_state:
        pending_badges.append(f"📄 {st.session_state.get('pending_txt_name', 'File')}")
    if pending_badges:
        st.caption("সংযুক্ত ফাইল প্রস্তুত: " + " | ".join(pending_badges))

# মূল চ্যাট ইনপুট বক্স
user_query = st.chat_input("Ask Gemini in Bangla or English, or use 🎙️ to speak...")

if user_query:
    img_attachment = st.session_state.pop("pending_img", None)
    img_name = st.session_state.pop("pending_img_name", "")
    pdf_attachment = st.session_state.pop("pending_pdf", None)
    pdf_name = st.session_state.pop("pending_pdf_name", "")
    txt_attachment = st.session_state.pop("pending_txt", "")
    txt_name = st.session_state.pop("pending_txt_name", "")

    prefix_tags = []
    if img_attachment is not None:
        prefix_tags.append(f"🖼️ *[{img_name}]*")
    if pdf_attachment is not None:
        prefix_tags.append(f"📕 *[{pdf_name}]*")
    if txt_attachment:
        prefix_tags.append(f"📄 *[{txt_name}]*")

    display_text = (" ".join(prefix_tags) + "\n\n" + user_query).strip() if prefix_tags else user_query

    with st.chat_message("user"):
        st.markdown(display_text)

    with st.chat_message("assistant"):
        with st.spinner("উত্তর তৈরি হচ্ছে..."):
            try:
                reply_text = process_user_submission(
                    display_msg=display_text,
                    prompt_text=user_query,
                    image_obj=img_attachment,
                    pdf_bytes=pdf_attachment,
                    doc_text=txt_attachment,
                )
                if reply_text:
                    st.markdown(reply_text)
            except Exception as e:
                st.error(f"ত্রুটি হয়েছে: {e}")
    st.rerun()
