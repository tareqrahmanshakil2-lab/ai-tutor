import streamlit as st
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
api_key = st.sidebar.text_input("Gemini API Key দাও:", type="password")

if api_key:
  genai.configure(api_key=api_key)
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

# Main Chat Interface
prompt = st.chat_input("প্রশ্নটি এখানে লেখো অথবা খাতার ছবি দিয়ে বলো...")

if prompt or uploaded_file:
  if not api_key:
    st.error("প্রথমে সাইডবারে আপনার Gemini API Key দিন!")
  else:
    try:
      # Using the correct working model
      model = genai.GenerativeModel("gemini-1.5-flash")

      content_to_send = []
      if prompt:
        content_to_send.append(prompt)

      if uploaded_file:
        image = Image.open(uploaded_file)
        content_to_send.append(image)
        st.image(image, caption="আপলোডকৃত ছবি/খাতা", width=300)

      if prompt:
        st.write(f"**প্রশ্ন:** {prompt}")

      with st.spinner("খাতা ও সমীকরণ বিশ্লেষণ করা হচ্ছে..."):
        response = model.generate_content(content_to_send)
        st.markdown("### উত্তর:")
        st.markdown(response.text)

    except Exception as e:
      st.error(f"একটি সমস্যা হয়েছে: {e}")
