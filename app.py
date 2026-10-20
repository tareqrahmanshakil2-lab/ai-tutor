import os
from google import genai
from google.genai import types
from PIL import Image
import streamlit as st

# ==========================================
# ১. সিস্টেম প্রম্পট (এআই-কে শিক্ষক ও সলভার বানানোর মূল ব্রেইন)
# ==========================================
SYSTEM_INSTRUCTION = """
তুমি একজন অত্যন্ত অভিজ্ঞ ইঞ্জিনিয়ারিং অ্যাডমিশন (BUET, CKRUET, SUST, IUT, DU) এবং HSC লেভেলের গণিত, পদার্থবিজ্ঞান ও রসায়ন শিক্ষক। 
তোমার দুটি প্রধান কাজ:

১. শিক্ষকের মতো খাতা দেখা (Answer Script Checking):
যখন কোনো শিক্ষার্থী তার হাতের লেখা খাতার ছবি বা সমাধান পাঠাবে:
- প্রথম লাইন থেকে শেষ লাইন পর্যন্ত প্রতিটি গাণিতিক ধাপ, সূত্র, চিহ্ন (+, -) এবং একক (SI Unit) খুঁটিয়ে দেখবে।
- কোনো লাইনে ভুল থাকলে ঠিক কোন লাইনে ভুল হয়েছে তা উদ্ধৃত করে দেখিয়ে দেবে। ভুলটি কি 'সূত্রের ভুল (Conceptual Error)' নাকি 'ক্যালকুলেশন বা তোলার ভুল (Transcription/Silly Error)' তা স্পষ্ট করে বলবে।
- বুয়েট (BUET) বা স্ট্যান্ডার্ড লিখিত পরীক্ষায় ১০ নম্বরের মধ্যে এই উত্তরের জন্য সে কত নম্বর পাবে (Partial Marking সহ), তা জানিয়ে দেবে।
- যে লাইনে ভুল হয়েছে, তার পর থেকে একদম সঠিক সমাধানটি কোনো লাইন স্কিপ না করে লিখে দেবে।

২. জটিল সমস্যার ব্যাখ্যামূলক ও ধাপে ধাপে সমাধান (Zero-Skip Problem Solving):
যখন কোনো শিক্ষার্থী একটি প্রশ্ন সমাধান করতে দেবে:
- মূল কনসেপ্ট ও থিওরি: অঙ্ক শুরু করার আগে এই অঙ্কে কোন সূত্র বা থিওরি কাজ করছে এবং কেন সেটি এখানে প্রযোজ্য, তা সহজ বাংলায় ব্যাখ্যা করবে।
- প্রদত্ত তথ্য (Given Data): প্রশ্নে কী কী দেওয়া আছে এবং কী বের করতে হবে তা সুন্দর করে সাজিয়ে লিখবে।
- ধাপে ধাপে সমাধান (Zero-Skip Steps): লিখিত পরীক্ষার খাতায় যেভাবে এক লাইনও স্কিপ না করে প্রতিটি ক্যালকুলেশন দেখাতে হয়, ঠিক সেভাবে প্রতিটি লাইন ভেঙে সমাধান করবে। কোনো মেন্টাল ম্যাথ বা শর্টকাট জাম্প করবে না। সকল সমীকরণ সুন্দর LaTeX ফরম্যাটে ($$...$$) লিখবে।
- এক্সাম টিপস (Common Trap): অঙ্কের শেষে শিক্ষার্থীরা সাধারণত এই অঙ্কে কোথায় ভুল করে এবং এমসিকিউ-তে দ্রুত চেক করার উপায় কী, তা ১-২ লাইনে বলে দেবে।
"""

# ==========================================
# ২. ওয়েব অ্যাপ ইন্টারফেস (Streamlit UI)
# ==========================================
st.set_page_config(page_title="Admission AI Examiner & Solver", page_icon="🎓", layout="wide")

st.title("🎓 ইঞ্জিনিয়ারিং অ্যাডমিশন এআই টিউটর ও এক্সামিনার")
st.write("যেকোনো জটিল ম্যাথ/ফিজিক্স প্রশ্ন করো অথবা হাতের লেখা খাতার ছবি আপলোড করে শিক্ষকের মতো খাতা চেক করিয়ে নাও!")

with st.sidebar:
    st.header("⚙️ সেটিংস")
    api_key = st.text_input("Gemini API Key দাও:", type="password", value=os.environ.get("GEMINI_API_KEY", ""))
    st.markdown("[এখান থেকে ফ্রি Gemini API Key নাও](https://aistudio.google.com/app/apikey)")
    
    st.subheader("📸 খাতার ছবি আপলোড করো")
    uploaded_file = st.file_uploader("হাতের লেখা খাতার বা প্রশ্নের ছবি (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="আপলোড করা খাতা", use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input("প্রশ্নটি এখানে লেখো অথবা খাতার ছবি দিয়ে বলো 'খাতাটা চেক করে দাও'...")

if user_prompt:
    if not api_key:
        st.error("দয়া করে বাম পাশের সাইডবারে তোমার Gemini API Key টি দাও!")
    else:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("খাতা ও সমীকরণ বিশ্লেষণ করা হচ্ছে..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    contents = [user_prompt]
                    if uploaded_file:
                        img = Image.open(uploaded_file)
                        contents.append(img)

                    response = client.models.generate_content(
                        model="gemini-2.5-pro",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            temperature=0.2,
                        )
                    )
                    
                    bot_reply = response.text
                    st.markdown(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                except Exception as e:
                    st.error(f"একটি সমস্যা হয়েছে: {e}")