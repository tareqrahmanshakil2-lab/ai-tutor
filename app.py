import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image

# Page Configuration
st.set_page_config(
    page_title="Shakil's Tutor - Engineering Admission AI Tutor",
    page_icon="🎓",
    layout="wide",
)

st.markdown(
    """
    <h1 style='text-align: center;'>🎓 ইঞ্জিনিয়ারিং অ্যাডমিশন এআই টিউটর ও এক্সামিনার</h1>
    <p style='text-align: center;'>যেকোনো জটিল ম্যাথ/ফিজিক্স প্রশ্ন করো অথবা খাতার ছবি আপলোড করে শিক্ষকের মতো খাতা চেক করিয়ে নাও!</p>
""",
    unsafe_allow_html=True,
)

# Sidebar for API Key & Image Upload
st.sidebar.markdown("## ⚙️ সেটিংস")

# Try loading API key from Streamlit secrets automatically, fallback to sidebar input
api_key = None
if "GEMINI_API_KEY" in st.secrets:
  api_key = st.secrets["GEMINI_API_KEY"]

user_api_key = st.sidebar.text_input(
    "Gemini API Key দাও:",
    value=api_key if api_key else "",
    type="password",
)

if user_api_key:
  genai.configure(api_key=user_api_key)
else:
  st.sidebar.warning(
      "দয়া করে আপনার Gemini API Key এখানে দিন অথবা Streamlit Secrets-এ সেট"
      " করুন।"
  )
  st.sidebar.markdown(
      "[এখানে থেকে ফ্রি Gemini API Key নাও]"
      "(https://aistudio.google.com/app/api-keys)"
  )

st.sidebar.markdown("---")
st.sidebar.markdown("## 📸 খাতা বা ছবি আপলোড")
uploaded_file = st.sidebar.file_uploader(
    "হাতের লেখা খাতার বা প্রশ্নের ছবি (JPG/PNG)", type=["jpg", "jpeg", "png"]
)

# Sidebar Voice Input Component (supports Bengali & English)
st.sidebar.markdown("---")
st.sidebar.markdown("## 🎙️ মাইক্রোফোন ইনপুট")
st.sidebar.caption("বাংলা বা ইংরেজিতে কথা বলুন:")

# Web Speech API Component
speech_component = """
<div style="font-family: sans-serif; text-align: center; background: #1e1e1e; padding: 10px; border-radius: 8px;">
    <select id="languageSelect" style="padding: 5px; border-radius: 4px; margin-bottom: 8px; width: 100%;">
        <option value="bn-BD">বাংলা (Bengali)</option>
        <option value="en-US">English (US)</option>
    </select>
    <br>
    <button id="startBtn" onclick="startDictation()" style="background-color: #ff4b4b; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold;">
        🎤 কথা বলা শুরু করুন
    </button>
    <p id="status" style="color: #aaa; font-size: 12px; margin-top: 5px;">বাটন চেপে কথা বলুন...</p>
</div>

<script>
    function startDictation() {
        if (window.hasOwnProperty('webkitSpeechRecognition')) {
            var recognition = new webkitSpeechRecognition();
            var lang = document.getElementById('languageSelect').value;
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = lang;
            
            document.getElementById('status').innerText = 'শুনছি... (কথা বলুন)';
            recognition.start();

            recognition.onresult = function(e) {
                var transcript = e.results[0][0].transcript;
                recognition.stop();
                document.getElementById('status').innerText = 'কথা রেকর্ড হয়েছে!';
                
                // Send recognized text to Streamlit
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: transcript
                }, '*');
            };

            recognition.onerror = function(e) {
                recognition.stop();
                document.getElementById('status').innerText = 'কোনো কথা বোঝা যায়নি, আবার চেষ্টা করুন।';
            };
        } else {
            document.getElementById('status').innerText = 'আপনার ব্রাউজারে মাইক্রোফোন সাপোর্ট করছে না। Chrome ব্রাউজার ব্যবহার করুন।';
        }
    }
</script>
"""

# Render speech component and get recognized text
voice_text = components.html(speech_component, height=140)

# Initialize Chat History in Session State
if "messages" not in st.session_state:
  st.session_state.messages = []

# Initialize Gemini Chat Session
if "chat_session" not in st.session_state:
  st.session_state.chat_session = None

# Configure Model if API Key is available
if user_api_key:
  try:
    model = genai.GenerativeModel("gemini-3.8-flash")
    if st.session_state.chat_session is None:
      st.session_state.chat_session = model.start_chat(history=[])
  except Exception as e:
    st.error(f"মডেল সেটআপ করতে সমস্যা হয়েছে: {e}")

# Display Past Chat History
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])
    if "image" in message and message["image"]:
      st.image(message["image"], caption="আপলোডকৃত খাতা/ছবি", width=300)

# Main Chat Input
text_prompt = st.chat_input("প্রশ্নটি এখানে লেখো অথবা মাইক্রোফোন ব্যবহার করো...")

# Determine effective prompt (either typed text or recognized voice)
prompt = text_prompt

if prompt or uploaded_file:
  if not user_api_key:
    st.error("প্রথমে আপনার Gemini API Key দিতে হবে!")
  else:
    current_content = []
    if prompt:
      current_content.append(prompt)

    image_to_display = None
    if uploaded_file:
      image = Image.open(uploaded_file)
      current_content.append(image)
      image_to_display = image

    user_display_text = (
        prompt if prompt else "📸 [একটি খাতা বা ছবি আপলোড করা হয়েছে]"
    )
    st.session_state.messages.append(
        {"role": "user", "content": user_display_text, "image": image_to_display}
    )

    with st.chat_message("user"):
      st.markdown(user_display_text)
      if image_to_display:
        st.image(image_to_display, caption="আপলোডকৃত ছবি", width=300)

    with st.chat_message("assistant"):
      with st.spinner("খাতা ও সমীকরণ বিশ্লেষণ করা হচ্ছে..."):
        try:
          response = st.session_state.chat_session.send_message(current_content)
          bot_reply = response.text
          st.markdown(bot_reply)

          st.session_state.messages.append(
              {"role": "assistant", "content": bot_reply, "image": None}
          )
        except Exception as e:
          st.error(f"একটি সমস্যা হয়েছে: {e}")
