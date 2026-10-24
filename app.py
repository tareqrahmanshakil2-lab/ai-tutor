# --- ৪. অনুমোদিত ফ্ল্যাশ মডেল ইঞ্জিন ---
def run_flash_engine(prompt_parts):
    if not st.session_state.api_key:
        raise ValueError("API Key is missing. Please set your Gemini API key in settings.")
    
    genai.configure(api_key=st.session_state.api_key)
    
    # সরাসরি স্থিতিশীল এবং প্রমাণিত মডেল ব্যবহার করা হচ্ছে
    model_name = st.session_state.get("selected_model", "gemini-1.5-flash")
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        # ফলব্যাক হিসেবে অন্য মডেল চেষ্টা করা
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt_parts)
            return response.text
        except Exception as err:
            raise RuntimeError(f"Gemini API Error: {err}")
