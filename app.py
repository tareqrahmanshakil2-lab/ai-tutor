import streamlit as st
import google.generativeai as genai
import json
import os

# --- ১. পেজ কনফিগারেশন ---
st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 AI Tutor")
st.caption("তোমার পার্সোনাল লার্নিং অ্যাসিস্ট্যান্ট — টেক্সট বা ভয়েসে যেকোনো প্রশ্ন করো!")

# --- ২. স্থায়ী চ্যাট হিস্ট্রি (ফাইল ভিত্তিক) লোড ও সেভ ফাংশন ---
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(messages):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# সেশন স্টেটে চ্যাট হিস্ট্রি ইনিশিয়ালাইজ করা
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# লাস্ট প্রসেসড অডিও ট্র্যাক করা (যাতে একই অডিও বারবার সেন্ড না হয়)
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# --- ৩. সাইডবার এবং স্থায়ী API Key সেটআপ ---
with st.sidebar:
    st.header("⚙️ সেটিংস")
    
    # Streamlit Secrets অথবা Environment Variable থেকে অটোমেটিক API Key নেওয়া
    api_key = st.secrets.get("GEMINI_API_KEY", None) if "GEMINI_API_KEY" in st.secrets else os.environ.get("GEMINI_API_KEY")
    
    if api_key:
        st.success("API Key স্বয়ংক্রিয়ভাবে সংযুক্ত রয়েছে!")
    else:
        api_key = st.text_input("Gemini API Key দাও:", type="password", help="স্থায়ীভাবে সেভ রাখতে Streamlit Secrets ব্যবহার করো।")
        st.info("💡 **টিপস:** বারবার API Key না লিখতে চাইলে Streamlit Cloud-এর **Settings -> Secrets**-এ গিয়ে `GEMINI_API_KEY = 'তোমার_কি'` লিখে সেভ করে রাখো।")

    st.divider()
    
    # মাইক্রোফোন ইনপুট (ভয়েস প্রশ্ন করার জন্য)
    st.subheader("🎙️ ভয়েস দিয়ে প্রশ্ন করো")
    audio_value = st.audio_input("মাইক্রোফোনে ক্লিক করে প্রশ্ন রেকর্ড করো:")
    
    st.divider()
    
    # চ্যাট ক্লিয়ার করার বাটন
    if st.button("🗑️ সব চ্যাট হিস্ট্রি মুছে ফেলো", use_container_width=True):
        st.session_state.messages = []
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        st.session_state.last_audio_id = None
        st.rerun()

# API Key না থাকলে সতর্কবার্তা দেখানো
if not api_key:
    st.warning("অনুগ্রহ করে বাম পাশের সাইডবারে তোমার Gemini API Key দাও অথবা Streamlit Secrets-এ যুক্ত করো।")
    st.stop()

# Gemini কনফিগার করা
genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction="তুমি একজন দক্ষ এবং বন্ধুসুলভ AI Tutor। ছাত্রছাত্রীদের যেকোনো প্রশ্ন সহজ বাংলায়, ধাপে ধাপে এবং স্পষ্টভাবে বুঝিয়ে দাও। গণিত বা বিজ্ঞানের সমস্যার ক্ষেত্রে সূত্র ও প্রতিটি ধাপ ভেঙে ব্যাখ্যা করো।"
)

# --- ৪. আগের সব চ্যাট হিস্ট্রি স্ক্রিনে দেখানো ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- ৫. ভয়েস ইনপুট (মাইক্রোফোন) প্রসেসিং ---
if audio_value is not None:
    # নতুন অডিও রেকর্ড হয়েছে কিনা তা চেক করা
    audio_bytes = audio_value.getvalue()
    current_audio_id = hash(audio_bytes)
    
    if current_audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = current_audio_id
        
        # ইউজারের মেসেজ দেখানো
        with st.chat_message("user"):
            st.markdown("🎤 *[ভয়েস মেসেজ পাঠানো হয়েছে]*")
            st.audio(audio_bytes, format="audio/wav")
            
        st.session_state.messages.append({
            "role": "user",
            "content": "🎤 *[ভয়েস প্রশ্ন]*"
        })
        
        # এআই থেকে উত্তর তৈরি করা
        with st.chat_message("assistant"):
            with st.spinner("তোমার ভয়েস শুনছি এবং উত্তর তৈরি করছি..."):
                try:
                    # আগের কথোপকথনের কনটেক্সট তৈরি করা
                    history_context = "\n".join(
                        [f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]]
                    )
                    
                    prompt_parts = [
                        f"পূর্ববর্তী কথোপকথন:\n{history_context}\n\nনিচের অডিওটি মনোযোগ দিয়ে শোনো। প্রথমে অডিওতে কী প্রশ্ন করা হয়েছে তা সংক্ষেপে উল্লেখ করো এবং এরপর বিস্তারিত উত্তর দাও।",
                        {"mime_type": "audio/wav", "data": audio_bytes}
                    ]
                    
                    response = model.generate_content(prompt_parts)
                    reply = response.text
                    st.markdown(reply)
                    
                    # হিস্ট্রিতে সেভ করা
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": reply
                    })
                    save_history(st.session_state.messages)
                except Exception as e:
                    st.error(f"ভয়েস প্রসেস করতে সমস্যা হয়েছে: {e}")

# --- ৬. টেক্সট ইনপুট প্রসেসিং ---
user_prompt = st.chat_input("তোমার প্রশ্ন এখানে লেখো...")

if user_prompt:
    # ইউজারের প্রশ্ন স্ক্রিনে দেখানো ও সেভ করা
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt
    })
    
    # এআই-এর উত্তর জেনারেট করা
    with st.chat_message("assistant"):
        with st.spinner("চিন্তা করছি..."):
            try:
                # Gemini চ্যাট ফরম্যাটে পুরনো হিস্ট্রি রূপান্তর করা
                gemini_history = []
                for m in st.session_state.messages[:-1]:
                    role = "user" if m["role"] == "user" else "model"
                    gemini_history.append({"role": role, "parts": [m["content"]]})
                
                chat = model.start_chat(history=gemini_history)
                response = chat.send_message(user_prompt)
                reply = response.text
                
                st.markdown(reply)
                
                # হিস্ট্রিতে সেভ করা
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply
                })
                save_history(st.session_state.messages)
            except Exception as e:
                st.error(f"উত্তর তৈরি করতে সমস্যা হয়েছে: {e}")
    generate_gemini_response(display_text, [user_prompt])
    st.rerun()
