import os
import streamlit as st
import google.generativeai as genai

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

# Try loading API key from Streamlit secrets first, otherwise from sidebar input
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
  st.sidebar.warning("দয়া করে আপনার Gemini API Key এখানে দিন।")
  st.sidebar.markdown(
      "[এখানে থেকে ফ্রি Gemini API Key নাও]"
      "(https://aistudio.google.com/app/api-keys)"
  )

st.sidebar.markdown("---")
st.sidebar.markdown("## 📸 খাতা বা ছবি আপলোড")
uploaded_file = st.sidebar.file_uploader(
    "হাতের লেখা খাতার বা প্রশ্নের ছবি (JPG/PNG)", type=["jpg", "jpeg", "png"]
)

# Initialize Chat History in Session State
if "messages" not in st.session_state:
  st.session_state.messages = []

# Initialize Gemini Chat Session
if "chat_session" not in st.session_state:
  st.session_state.chat_session = None

# Configure Model if API Key is available
if user_api_key:
  try:
    # Using the updated model name
    model = genai.GenerativeModel("gemini-3.8-flash")
    if st.session_state.chat_session is None:
      st.session_state.chat_session = model.start_chat(history=[])
  except Exception as e:
    st.error(f"মডেল সেটআপ করতে সমস্যা হয়েছে: {e}")

# Display Prior Chat History
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])
    if "image" in message and message["image"]:
      st.image(message["image"], caption="আপলোডকৃত খাতা/ছবি", width=300)

# Handle User Input / Question
prompt = st.chat_input("প্রশ্নটি এখানে লেখো অথবা খাতার ছবি দিয়ে বলো 'খাতাটা চেক করে দাও'...")

if prompt or uploaded_file:
  if not user_api_key:
    st.error("প্রথমে সাইডবারে আপনার Gemini API Key দিন!")
  else:
    # Prepare user content
    current_content = []
    if prompt:
      current_content.append(prompt)
    else:
      current_content.append("এই খাতা বা ছবিটি দেখে মূল্যায়ন করো:")

    image_to_display = None
    if uploaded_file:
      from PIL import Image

      image = Image.open(uploaded_file)
      current_content.append(image)
      image_to_display = image

    # Display User Message
    user_display_text = prompt if prompt else "📸 [একটি খাতা/ছবি আপলোড করা হয়েছে]"
    st.session_state.messages.append(
        {"role": "user", "content": user_display_text, "image": image_to_display}
    )
    with st.chat_message("user"):
      st.markdown(user_display_text)
      if image_to_display:
        st.image(image_to_display, caption="আপলোডকৃত ছবি", width=300)

    # Generate AI Response
    with st.chat_message("assistant"):
      with st.spinner("খাতা ও সমীকরণ বিশ্লেষণ করা হচ্ছে..."):
        try:
          response = st.session_state.chat_session.send_message(current_content)
          bot_reply = response.text
          st.markdown(bot_reply)

          # Save Assistant Response to History
          st.session_state.messages.append(
              {"role": "assistant", "content": bot_reply, "image": None}
          )
        except Exception as e:
          error_msg = f"একটি সমস্যা হয়েছে: {e}"
          st.error(error_msg)
