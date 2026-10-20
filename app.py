import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
from gtts import gTTS
import json
import os
import uuid
import io
from datetime import datetime

# --- ১. পেজ কনফিগারেশন ---
st.set_page_config(
    page_title="AI Tutor Pro - Gemini Edition",
    page_icon="✨",
    layout="wide"
)

# কাস্টম সিএসএস (সুন্দর ইন্টারফেসের জন্য)
st.markdown("""
<style>
    .stButton button {
        border-radius: 8px;
    }
    div[data-testid="stSidebarContent"] {
        padding-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- ২. ডাটাবেস / মাল্টি-সেশন চ্যাট হিস্ট্রি ফাংশন ---
SESSIONS_FILE = "all_chat_sessions.json"

def load_all_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data:
                    return data
        except Exception:
            pass
    # ডিফল্ট প্রথম চ্যাট সেশন তৈরি করা
    default_id = str(uuid.uuid4())
    return {
        default_id: {
            "title": "নতুন চ্যাট",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "messages": []
        }
    }

def save_all_sessions(sessions):
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def create_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.chat_sessions[new_id] = {
        "title": "নতুন চ্যাট",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "messages": []
    }
    st.session_state.current_session_id = new_id
    st.session_state.last_audio_id = None
    save_all_sessions(st.session_state.chat_sessions)

# সেশন স্টেট ইনিশিয়ালাইজেশন
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = load_all_sessions()

if "current_session_id" not in st.session_state or st.session_state.current_session_id not in st.session_state.chat_sessions:
    st.session_state.current_session_id = list(st.session_state.chat_sessions.keys())[-1]

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# বর্তমান সেশনের তথ্য নেওয়া
current_session = st.session_state.chat_sessions[st.session_state.current_session_id]

# --- ৩. সাইডবার (New Chat, History, Settings, Multimodal Tools) ---
with st.sidebar:
    st.title("✨ AI Tutor Pro")
    
    # + নতুন চ্যাট বাটন
    if st.button("➕ নতুন চ্যাট (New Chat)", use_container_width=True, type="primary"):
        create_new_chat()
        st.rerun()

    st.divider()

    # আগের চ্যাটগুলোর তালিকা (Chat History List)
    st.subheader("💬 চ্যাট হিস্ট্রি")
    session_ids = list(st.session_state.chat_sessions.keys())[::-1] # নতুনগুলো উপরে থাকবে
    
    for s_id in session_ids:
        s_data = st.session_state.chat_sessions[s_id]
        col1, col2 = st.columns([4, 1])
        with col1:
            is_active = (s_id == st.session_state.current_session_id)
            btn_label = f"🟢 {s_data['title']}" if is_active else f"📄 {s_data['title']}"
            if st.button(btn_label, key=f"chat_{s_id}", use_container_width=True):
                st.session_state.current_session_id = s_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{s_id}", help="এই চ্যাটটি মুছে ফেলো"):
                del st.session_state.chat_sessions[s_id]
                if not st.session_state.chat_sessions:
                    create_new_chat()
                elif st.session_state.current_session_id == s_id:
                    st.session_state.current_session_id = list(st.session_state.chat_sessions.keys())[-1]
                save_all_sessions(st.session_state.chat_sessions)
                st.rerun()

    st.divider()

    # 📎 ফাইল ও ছবি আপলোড (Gemini Multimodal)
    st.subheader("📎 ফাইল ও ছবি যুক্ত করো")
    uploaded_file = st.file_uploader(
        "ছবি (JPG/PNG), PDF বা Text ফাইল আপলোড করো:",
        type=["png", "jpg", "jpeg", "webp", "pdf", "txt", "py", "cpp", "c", "csv"]
    )
    
    extracted_file_text = ""
    uploaded_image = None
    
    if uploaded_file is not None:
        file_type = uploaded_file.type
        if "image" in file_type:
            uploaded_image = Image.open(uploaded_file)
            st.image(uploaded_image, caption="আপলোড করা ছবি", use_container_width=True)
        elif "pdf" in file_type:
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    extracted_file_text += page.extract_text() + "\n"
                st.success(f"PDF লোড হয়েছে ({len(pdf_reader.pages)} পৃষ্ঠা)")
            except Exception as e:
                st.error(f"PDF পড়তে সমস্যা হয়েছে: {e}")
        else:
            try:
                extracted_file_text = uploaded_file.read().decode("utf-8")
                st.success(f"'{uploaded_file.name}' ফাইলটি লোড হয়েছে!")
            except Exception as e:
                st.error(f"ফাইল পড়তে সমস্যা হয়েছে: {e}")

    st.divider()

    # 🎙️ মাইক্রোফোন (Voice Input)
    st.subheader("🎙️ ভয়েস ইনপুট")
    audio_value = st.audio_input("মাইক্রোফোনে ক্লিক করে প্রশ্ন বলো:")
    enable_tts = st.checkbox("🔊 এআই-এর উত্তর ভয়েসে শোনাও", value=False)

    st.divider()

    # 🧠 জেমিনি মডেল ও মোড সেটিংস
    with st.expander("⚙️ মডেল, মোড ও API সেটিংস", expanded=False):
        # API Key অটো ডিটেকশন
        api_key = None
        try:
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
        
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")

        if api_key:
            st.success("🔑 API Key স্বয়ংক্রিয়ভাবে সংযুক্ত!")
        else:
            api_key = st.text_input("Gemini API Key দাও:", type="password")
            st.caption("স্থায়ীভাবে সেভ করতে Streamlit Cloud-এর Settings -> Secrets-এ গিয়ে `GEMINI_API_KEY = 'তোমার_কি'` যুক্ত করো।")

        # মডেল নির্বাচন
        selected_model = st.selectbox(
            "মডেল বেছে নাও:",
            ["gemini-2.8-flash", "gemini-2.5-pro"],
            index=0,
            help="Flash দ্রুত উত্তর দেয়, আর Pro জটিল গণিত ও লজিক্যাল সমস্যার গভীর সমাধান দেয়।"
        )

        # পার্সোনা বা মোড নির্বাচন
        tutor_mode = st.selectbox(
            "টিউটর মোড (Persona):",
            [
                "🎓 সাধারণ AI টিউটর (ধাপে ধাপে সহজ ব্যাখ্যা)",
                "📐 বিজ্ঞান ও গণিত সলভার (সূত্র ও জিরো-স্কিপ ক্যালকুলেশন)",
                "📝 খাতা পরীক্ষক / Examiner (হাতের লেখা ও উত্তর মূল্যায়ন)",
                "💻 কোডিং ও প্রোগ্রামিং এক্সপার্ট (বাগ ফিক্স ও অপটিমাইজেশন)"
            ]
        )

        temperature = st.slider("সৃজনশীলতা (Temperature):", 0.0, 1.0, 0.4, 0.1)

    # চ্যাট ডাউনলোড বাটন
    if current_session["messages"]:
        chat_export_text = "\n\n".join(
            [f"{'ইউজার' if m['role']=='user' else 'AI Tutor'}: {m['content']}" for m in current_session["messages"]]
        )
        st.download_button(
            label="📥 এই চ্যাটটি ডাউনলোড করো (.txt)",
            data=chat_export_text,
            file_name=f"{current_session['title']}.txt",
            mime="text/plain",
            use_container_width=True
        )

# --- ৪. মেইন স্ক্রিন ও API Key চেক ---
st.header(f"✨ {current_session['title']}")
st.caption(f"মডেল: `{selected_model}` | মোড: `{tutor_mode}`")

if not api_key:
    st.warning("⚠️ অনুগ্রহ করে বাম পাশের সাইডবারের **'মডেল, মোড ও API সেটিংস'** অপশনে গিয়ে তোমার Gemini API Key দাও অথবা Streamlit Secrets-এ সেভ করো।")
    st.stop()

# মোড অনুযায়ী সিস্টেম ইনস্ট্রাকশন সেট করা
system_prompts = {
    "🎓 সাধারণ AI টিউটর (ধাপে ধাপে সহজ ব্যাখ্যা)": "তুমি একজন দক্ষ এবং বন্ধুসুলভ AI Tutor। যেকোনো প্রশ্ন সহজ বাংলায়, স্পষ্ট উদাহরণসহ ধাপে ধাপে বুঝিয়ে দাও।",
    "📐 বিজ্ঞান ও গণিত সলভার (সূত্র ও জিরো-স্কিপ ক্যালকুলেশন)": "তুমি একজন অভিজ্ঞ পদার্থবিজ্ঞান, রসায়ন ও উচ্চতর গণিতের শিক্ষক। যেকোনো গাণিতিক সমস্যার ক্ষেত্রে প্রথমে প্রদত্ত উপাত্ত, প্রয়োজনীয় সূত্র, মূল তত্ত্ব এবং কোনো লাইন স্কিপ না করে প্রতিটি ক্যালকুলেশন ধাপে ধাপে LaTeX ফরম্যাটে সমাধান করে দেখাও।",
    "📝 খাতা পরীক্ষক / Examiner (হাতের লেখা ও উত্তর মূল্যায়ন)": "তুমি একজন অভিজ্ঞ পরীক্ষক। ইউজার তার হাতের লেখা বা উত্তরের ছবি/টেক্সট দিলে প্রতিটি লাইন মনোযোগ দিয়ে যাচাই করো। কোথায় ভুল হয়েছে তা চিহ্নিত করো, নম্বর দাও এবং সঠিক সমাধানটি ধাপে ধাপে লিখে দাও।",
    "💻 কোডিং ও প্রোগ্রামিং এক্সপার্ট (বাগ ফিক্স ও অপটিমাইজেশন)": "তুমি একজন সিনিয়র সফটওয়্যার ইঞ্জিনিয়ার। পরিষ্কার, বাগ-মুক্ত ও অপটিমাইজড কোড লেখো এবং কোডের প্রতিটি অংশ সহজ বাংলায় ব্যাখ্যা করো।"
}

genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    model_name=selected_model,
    system_instruction=system_prompts[tutor_mode],
    generation_config={"temperature": temperature}
)

# টেক্সট টু স্পিচ (TTS) হেল্পার ফাংশন
def play_tts(text):
    try:
        clean_text = text.replace("*", "").replace("#", "").replace("`", "")[:1000]
        tts = gTTS(text=clean_text, lang="bn")
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        st.audio(audio_fp, format="audio/mp3")
    except Exception:
        pass

# --- ৫. বর্তমান চ্যাটের পুরনো মেসেজগুলো দেখানো ---
if not current_session["messages"]:
    st.info("👋 হ্যালো! নতুন চ্যাটে স্বাগতম। নিচে লিখে, মাইক্রোফোনে বলে অথবা সাইডবারে ছবি/PDF আপলোড করে তোমার যেকোনো প্রশ্ন করতে পারো।")

for msg in current_session["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- ৬. উত্তর জেনারেট করার কমন ফাংশন (Streaming সহ) ---
def generate_gemini_response(user_display_text, prompt_parts):
    # প্রথম মেসেজ হলে চ্যাটের নাম (Title) স্বয়ংক্রিয়ভাবে আপডেট করা
    if len(current_session["messages"]) == 0:
        short_title = user_display_text.replace("🎤 *[ভয়েস প্রশ্ন]*", "ভয়েস আলোচনা").strip()[:28]
        current_session["title"] = short_title if short_title else "নতুন আলোচনা"

    # ইউজারের মেসেজ সেভ করা
    current_session["messages"].append({
        "role": "user",
        "content": user_display_text
    })

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            # আগের মেসেজগুলোর কনটেক্সট যুক্ত করা
            history_context = "\n".join(
                [f"{'User' if m['role']=='user' else 'Assistant'}: {m['content']}" for m in current_session["messages"][-10:-1]]
            )
            
            final_payload = []
            if history_context:
                final_payload.append(f"পূর্ববর্তী কথোপকথনের সারাংশ:\n{history_context}\n---")
            
            if extracted_file_text:
                final_payload.append(f"আপলোড করা ফাইলের বিষয়বস্তু:\n{extracted_file_text[:15000]}\n---")
                
            if uploaded_image is not None:
                final_payload.append(uploaded_image)
                
            final_payload.extend(prompt_parts)

            # স্ট্রিমিং রেসপন্স (আসল জেমিনির মতো টাইপিং ইফেক্ট)
            response = model.generate_content(final_payload, stream=True)
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)

            # অডিও উত্তর শোনানো (যদি চেকবক্স অন থাকে)
            if enable_tts and full_response:
                play_tts(full_response)

            # অ্যাসিস্ট্যান্টের মেসেজ সেভ করা
            current_session["messages"].append({
                "role": "assistant",
                "content": full_response
            })
            save_all_sessions(st.session_state.chat_sessions)

        except Exception as e:
            st.error(f"উত্তর তৈরি করতে সমস্যা হয়েছে: {e}")

# --- ৭. মাইক্রোফোন (Voice Input) প্রসেসিং ---
if audio_value is not None:
    audio_bytes = audio_value.getvalue()
    current_audio_id = hash(audio_bytes)
    
    if current_audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = current_audio_id
        
        with st.chat_message("user"):
            st.markdown("🎤 *[ভয়েস মেসেজ পাঠানো হয়েছে]*")
            st.audio(audio_bytes, format="audio/wav")
            
        voice_prompt = [
            "নিচের অডিওটি মনোযোগ দিয়ে শোনো। প্রথমে ইউজার কী প্রশ্ন করেছে তা এক লাইনে লেখো এবং তারপর বিস্তারিত উত্তর দাও।",
            {"mime_type": "audio/wav", "data": audio_bytes}
        ]
        generate_gemini_response("🎤 *[ভয়েস প্রশ্ন]*", voice_prompt)
        st.rerun()

# --- ৮. টেক্সট চ্যাট ইনপুট প্রসেসিং ---
user_prompt = st.chat_input("জেমিনিকে যেকোনো প্রশ্ন করো...")

if user_prompt:
    display_text = user_prompt
    if uploaded_file is not None:
        display_text = f"📎 *[{uploaded_file.name}]* \n\n{user_prompt}"
        
    with st.chat_message("user"):
        st.markdown(display_text)
        
    generate_gemini_response(display_text, [user_prompt])
    st.rerun()
