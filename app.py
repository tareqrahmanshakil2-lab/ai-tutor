import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import uuid
from datetime import datetime

# --- ১. পেজ কনফিগারেশন ---
st.set_page_config(
    page_title="Gemini Workspace AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ২. ডার্ক থিম সিএসএস ডিজাইন (Gemini UI Inspired) ---
st.markdown("""
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
    }
    .welcome-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 500;
        color: #e3e3e3;
        margin-top: 6vh;
        margin-bottom: 1.5rem;
    }
    div[data-testid="stChatMessage"] {
        background-color: rgba(30, 31, 32, 0.65) !important;
        border-radius: 16px !important;
        padding: 12px 18px !important;
        margin-bottom: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .section-label {
        font-size: 12px;
        color: #8e918f;
        padding-left: 12px;
        margin-top: 12px;
        margin-bottom: 4px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #1e1f20 !important;
        color: #e3e3e3 !important;
        border: 1px solid #3c4043 !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- ৩. ডাটা স্টোরেজ ও সেশন হ্যান্ডলিং ---
DATA_FILE = "gemini_workspace_data.json"
KEY_FILE = ".gemini_flash_key.txt"

def load_workspace():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "chats" in data:
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
                "messages": []
            }
        },
        "notebooks": ["পদার্থবিজ্ঞান নোটবুক", "উচ্চতর গণিত নোটবুক", "Web Dev Notebook"],
        "scheduled_tasks": [{"task": "Review daily ML research papers at 8 PM"}],
        "custom_instruction": "তুমি একজন দক্ষ AI সহকারী। বাংলায় স্পষ্ট, নির্ভুল এবং ধাপে ধাপে উত্তর দাও।"
    }

def save_workspace(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ.get("GEMINI_API_KEY")
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""

def save_api_key(key):
    try:
        with open(KEY_FILE, "w", encoding="utf-8") as f:
            f.write(key.strip())
    except Exception:
        pass

if "workspace" not in st.session_state:
    st.session_state.workspace = load_workspace()

ws = st.session_state.workspace

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
            "messages": []
        }
        st.session_state.current_chat_id = new_id

if "active_nav" not in st.session_state:
    st.session_state.active_nav = "New chat"

if "interaction_mode" not in st.session_state:
    st.session_state.interaction_mode = "Chat"

if "api_key" not in st.session_state:
    st.session_state.api_key = load_api_key()

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gemini-1.5-flash"

if "search_filter" not in st.session_state:
    st.session_state.search_filter = ""

def start_new_chat(notebook_name=None):
    new_id = str(uuid.uuid4())
    ws["chats"][new_id] = {
        "title": "New chat",
        "mode": st.session_state.interaction_mode,
        "notebook": notebook_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "messages": []
    }
    st.session_state.current_chat_id = new_id
    st.session_state.active_nav = "New chat"
    save_workspace(ws)

# --- ৪. অনুমোদিত ফ্ল্যাশ মডেল ইঞ্জিন (নিরাপদ ও সরাসরি) ---
def run_flash_engine(prompt_parts):
    if not st.session_state.api_key:
        raise ValueError("API Key is missing. Please set your Gemini API key in settings.")
    
    genai.configure(api_key=st.session_state.api_key)
    model_name = st.session_state.get("selected_model", "gemini-1.5-flash")
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt_parts)
            return response.text
        except Exception as err:
            raise RuntimeError(f"Gemini API Error: {err}")

# --- ৫. সাইডবার নেভিগেশন ও ডিজাইন ---
with st.sidebar:
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("### ✨ Gemini Workspace")
    with c2:
        with st.popover("🔍"):
            st.session_state.search_filter = st.text_input("চ্যাট খুঁজুন...", value=st.session_state.search_filter)

    if st.button("📝 New chat", use_container_width=True):
        start_new_chat()
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

    st.markdown('<div class="section-label">Notebooks</div>', unsafe_allow_html=True)
    with st.popover("➕ New notebook", use_container_width=True):
        nb_name = st.text_input("নতুন নোটবুকের নাম:")
        if st.button("তৈরি করো") and nb_name:
            if nb_name not in ws["notebooks"]:
                ws["notebooks"].append(nb_name)
                save_workspace(ws)
            start_new_chat(notebook_name=nb_name)
            st.rerun()

    for nb in ws["notebooks"]:
        if st.button(f"📓 {nb}", key=f"nb_{nb}", use_container_width=True):
            start_new_chat(notebook_name=nb)
            st.rerun()

    st.markdown('<div class="section-label">Recent Chats</div>', unsafe_allow_html=True)
    chat_ids = list(ws["chats"].keys())[::-1]
    for cid in chat_ids:
        chat_item = ws["chats"][cid]
        if st.session_state.search_filter and st.session_state.search_filter.lower() not in chat_item["title"].lower():
            continue
        col_title, col_del = st.columns([5, 1])
        with col_title:
            dot = "🔵 " if cid == st.session_state.current_chat_id else ""
            if st.button(f"{dot}{chat_item['title'][:24]}", key=f"hist_{cid}", use_container_width=True):
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
        st.markdown("🟢 **প্রোফাইল** \n<span style='font-size:11px;color:#8e918f;'>Gemini Engine • Active</span>", unsafe_allow_html=True)
    with p2:
        with st.popover("🔑"):
            st.markdown("**API Key আপডেট**")
            new_key = st.text_input("Gemini API Key:", value=st.session_state.api_key, type="password")
            if new_key != st.session_state.api_key:
                st.session_state.api_key = new_key
                save_api_key(new_key)
                st.success("API Key সংরক্ষিত!")

# --- ৬. বিভিন্ন ট্যাব বা মোড ভিউ ---
if not st.session_state.api_key:
    st.warning("👈 শুরু করতে সাইডবারের নিচে **⚙️ (সেটিংস)** অথবা **API Key** পপওভারে গিয়ে আপনার বৈধ **Gemini API Key** প্রদান করুন।")

if st.session_state.active_nav == "Library":
    st.subheader("🗂️ Workspace Library")
    for cid, cdata in list(ws["chats"].items())[::-1]:
        with st.expander(f"📄 {cdata['title']} ({cdata.get('created_at', '')})"):
            st.write(f"মেশিন মোড: {cdata.get('mode', 'Chat')} | নোটবুক: {cdata.get('notebook', 'None')} | মেসেজ সংখ্যা: {len(cdata.get('messages', []))}")
            if st.button("এই চ্যাটটি ওপেন করো", key=f"lib_{cid}"):
                st.session_state.current_chat_id = cid
                st.session_state.active_nav = "New chat"
                st.rerun()
    st.stop()

elif st.session_state.active_nav == "Images":
    st.subheader("🖼️ Images & Handwriting Analysis")
    img_file = st.file_uploader("ছবি বা খাতার পাতা আপলোড করুন:", type=["png", "jpg", "jpeg", "webp"])
    if img_file:
        img_obj = Image.open(img_file)
        st.image(img_obj, width=450)
        img_q = st.text_input("ছবি সম্পর্কিত প্রশ্ন লিখুন:", value="এই ছবি বা খাতাটি বিশ্লেষণ করে বিস্তারিত বুঝিয়ে দাও।")
        if st.button("বিশ্লেষণ শুরু করুন"):
            with st.spinner("এআই বিশ্লেষণ করছে..."):
                try:
                    ans = run_flash_engine([img_q, img_obj])
                    st.markdown("### ফলাফল:")
                    st.markdown(ans)
                except Exception as e:
                    st.error(f"ত্রুটি: {e}")
    st.stop()

elif st.session_state.active_nav == "Scheduled":
    st.subheader("🕒 Scheduled Tasks & Reminders")
    new_task = st.text_input("নতুন টাস্ক বা রিমাইন্ডার লিখুন:")
    if st.button("যোগ করুন") and new_task:
        ws["scheduled_tasks"].append({"task": new_task})
        save_workspace(ws)
        st.success("টাস্ক যুক্ত হয়েছে!")
        st.rerun()
    for idx, t in enumerate(ws["scheduled_tasks"]):
        st.markdown(f"✅ {idx+1}. {t['task']}")
    st.stop()

elif st.session_state.active_nav == "Customize":
    st.subheader("⚙️ Customize Settings & System Prompts")
    custom_inst = st.text_area("সিস্টেম ইনস্ট্রাকশন (AI Persona):", value=ws["custom_instruction"], height=120)
    api_k = st.text_input("Gemini API Key:", value=st.session_state.api_key, type="password")
    
    st.markdown("### মডেল নির্বাচন")
    model_choice = st.selectbox(
        "ডিফল্ট ফ্ল্যাশ ইঞ্জিন মডেল:", 
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
        index=0
    )
    
    if st.button("পরিবর্তনগুলো সেভ করুন"):
        ws["custom_instruction"] = custom_inst
        st.session_state.api_key = api_k
        st.session_state.selected_model = model_choice
        save_api_key(api_k)
        save_workspace(ws)
        st.success("সেটিংস সফলভাবে সংরক্ষিত হয়েছে!")
    st.stop()

elif st.session_state.active_nav == "More":
    st.subheader("••• Advanced Workspace Tools")
    if st.button("সকল চ্যাট হিস্ট্রি মুছে ফেলুন"):
        ws["chats"] = {}
        start_new_chat()
        st.success("সকল হিস্ট্রি রিসেট করা হয়েছে!")
        st.rerun()
    st.stop()

# --- ৭. মেইন চ্যাট ইন্টারফেস ---
current_chat = ws["chats"][st.session_state.current_chat_id]

def process_user_submission(display_msg, prompt_text, image_obj=None, audio_bytes=None, doc_text=""):
    if not st.session_state.api_key:
        st.error("অনুগ্রহ করে আগে API Key সেট করুন।")
        return

    if len(current_chat["messages"]) == 0:
        clean_title = display_msg.replace("🎤 *[ভয়েস প্রশ্ন]*", "ভয়েস আলোচনা").strip()[:32]
        current_chat["title"] = clean_title if clean_title else "নতুন আলোচনা"

    current_chat["messages"].append({"role": "user", "content": display_msg})

    with st.chat_message("assistant"):
        with st.spinner("উত্তর তৈরি হচ্ছে..."):
            try:
                history_context = "\n".join(
                    [f"{'User' if m['role']=='user' else 'Gemini'}: {m['content']}" for m in current_chat["messages"][-10:-1]]
                )
                
                full_prompt = f"{ws['custom_instruction']}\n\n"
                if history_context:
                    full_prompt += f"পূর্ববর্তী আলোচনা:\n{history_context}\n---\n"
                if doc_text:
                    full_prompt += f"ফাইল তথ্য:\n{doc_text[:10000]}\n---\n"
                full_prompt += f"প্রশ্ন: {prompt_text}"

                payload = [full_prompt]
                if image_obj is not None:
                    payload.append(image_obj)
                if audio_bytes is not None:
                    payload.append({"mime_type": "audio/wav", "data": audio_bytes})

                reply = run_flash_engine(payload)
                st.markdown(reply)

                current_chat["messages"].append({"role": "assistant", "content": reply})
                save_workspace(ws)
            except Exception as e:
                st.error(f"ত্রুটি হয়েছে: {e}")

# যদি চ্যাট খালি থাকে তবে ওয়েলকাম স্ক্রিন দেখাবে
if len(current_chat["messages"]) == 0:
    st.markdown('<div class="welcome-title">Where should we start?</div>', unsafe_allow_html=True)

    c_l, c_m, c_r = st.columns([1, 2.5, 1])
    with c_m:
        b1, b2, b3 = st.columns([1, 2, 1])
        with b1:
            with st.popover("➕"):
                attached_file = st.file_uploader("ফাইল বা ছবি দিন", type=["png", "jpg", "txt", "pdf"], key="home_up")
                if attached_file:
                    if attached_file.type.startswith("image/"):
                        img = Image.open(attached_file)
                        st.session_state['pending_img'] = img
                        st.success("ছবি আপলোড হয়েছে!")
                    else:
                        txt_data = attached_file.read().decode("utf-8", errors="ignore")
                        st.session_state['pending_txt'] = txt_data
                        st.success("টেক্সট ফাইল লোড হয়েছে!")
        with b2:
            st.button("⚡ Flash Engine Active", disabled=True, use_container_width=True)
        with b3:
            with st.popover("🎙️"):
                if hasattr(st, "audio_input"):
                    voice_input = st.audio_input("ভয়েস রেকর্ড:", key="home_mic")
                    if voice_input:
                        st.session_state['pending_audio'] = voice_input.read()
                        st.success("অডিও রেকর্ড সম্পন্ন!")
                else:
                    voice_up = st.file_uploader("অডিও আপলোড", type=["wav", "mp3"], key="home_mic_up")
                    if voice_up:
                        st.session_state['pending_audio'] = voice_up.read()
                        st.success("অডিও ফাইল সংযোজিত!")

        m1, m2 = st.columns([1, 1])
        with m1:
            if st.button("💬 Chat Mode", use_container_width=True):
                st.session_state.interaction_mode = "Chat"
        with m2:
            if st.button("⚡ Task Solver Mode", use_container_width=True):
                st.session_state.interaction_mode = "Task"

        st.write("")
        if st.button("📖 Explain calculus integration simply", use_container_width=True):
            process_user_submission("Explain calculus integration simply", "ক্যালকুলাসের ইন্টিগ্রেশন সহজ বাংলায় বাস্তব উদাহরণসহ বুঝিয়ে দাও।")
            st.rerun()
        if st.button("💡 Plan a productive daily study schedule", use_container_width=True):
            process_user_submission("Plan a productive daily study schedule", "প্রতিদিনের পড়াশোনার একটি চমৎকার ও কার্যকরী রুটিন তৈরি করে দাও।")
            st.rerun()
else:
    for msg in current_chat["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# মূল ইনপুট বার
user_query = st.chat_input("Ask Gemini or give a prompt...")    

if user_query:
    with st.chat_message("user"):
        st.markdown(user_query)
    
    img_attachment = st.session_state.pop('pending_img', None)
    txt_attachment = st.session_state.pop('pending_txt', "")
    audio_attachment = st.session_state.pop('pending_audio', None)
    
    process_user_submission(
        user_query, 
        user_query, 
        image_obj=img_attachment, 
        audio_bytes=audio_attachment, 
        doc_text=txt_attachment
    )
    st.rerun()
