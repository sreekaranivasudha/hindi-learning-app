import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from gtts import gTTS
import io

st.set_page_config(page_title="बाल मित्र (Hindi Learner)", page_icon="🎒", layout="wide")
st.title("🎒 बाल मित्र - Hindi Learning Buddy")

# Initialize Gemini Client
@st.cache_resource
def get_gemini_client():
    return genai.Client()

try:
    client = get_gemini_client()
except Exception:
    st.error("API Key missing! Please set GEMINI_API_KEY in Streamlit Advanced Settings.")
    client = None

# Comprehensive system prompt guiding Gemini on how to handle text, images, and audio
SYSTEM_INSTRUCTION = (
    "You are a warm, encouraging, and patient scheduling and learning assistant for a child. "
    "Speak entirely in clear, friendly Hindi (Devanagari script). Keep sentences short and easy to understand. "
    "Actively praise the child to build confidence. "
    "CRITICAL IMAGE RULE: If the user uploads an image, it is a photo of their Hindi handwriting. "
    "Transcribe it, point out any spelling or grammar errors gently, and explain the correction in simple Hindi. "
    "CRITICAL AUDIO RULE: If the user sends audio, listen to what they said in Hindi and reply normally to their conversation."
)

if "chat_session" not in st.session_state and client:
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to generate spoken audio safely in Hindi
def play_hindi_speech(text_to_speak):
    try:
        tts = gTTS(text=text_to_speak, lang='hi', slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        st.audio(audio_fp, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.error("Could not generate speech output right now.")

# --- SIDEBAR: INTERFACE FOR HANDWRITING ---
st.sidebar.header("📝 2. Check Handwriting")
st.sidebar.write("Upload a picture of your Hindi writing here!")
uploaded_file = st.sidebar.file_uploader("Choose a photo...", type=["jpg", "jpeg", "png"])

if uploaded_file and client:
    img = Image.open(uploaded_file)
    st.sidebar.image(img, caption="Your Writing", use_container_width=True)
    if st.sidebar.button("Analyze My Writing (गलतियां सुधारें)"):
        with st.spinner("Gemini Teacher is analyzing your writing..."):
            # FIX: Send ONLY the PIL Image object directly. System instructions tell it what to do.
            response = st.session_state.chat_session.send_message(img)
            st.session_state.messages.append({"role": "user", "text": "📸 [Uploaded a photo of my handwriting]"})
            st.session_state.messages.append({"role": "assistant", "text": response.text})
            st.rerun()

# --- MAIN PAGE: INTERFACE FOR VOICE CONVERSATION ---
st.subheader("🗣️ 1. Have a Conversation")

# Display past chat history along with an individual play button for each message
for index, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["text"])
        if msg["role"] == "assistant":
            if st.button("🔊 Listen again (दोबारा सुनें)", key=f"play_{index}"):
                play_hindi_speech(msg["text"])

# Voice Input Widget
audio_file = st.audio_input("Tap the microphone below to talk in Hindi:")

if audio_file and client:
    with st.spinner("Processing your voice..."):
        audio_bytes = audio_file.read()
        
        # DYNAMIC FIX: Automatically detect if it's audio/wav, audio/webm, or audio/ogg
        detected_mime_type = audio_file.type  
        
        # Create the audio part with the correct format matching your browser
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=detected_mime_type)
        
        try:
            response = st.session_state.chat_session.send_message(audio_part)
            st.session_state.messages.append({"role": "user", "text": "🎤 [Sent a voice message]"})
            st.session_state.messages.append({"role": "assistant", "text": response.text})
            st.rerun()
        except Exception as api_err:
            st.error(f"Google API Error: {api_err}")
            st.write("Tip: If voice errors persist, try typing in the chat bar below!")

# Text fallback input
user_text = st.chat_input("Or type your message here...")
if user_text and client:
    st.session_state.messages.append({"role": "user", "text": user_text})
    with st.spinner("Thinking..."):
        response = st.session_state.chat_session.send_message(user_text)
        st.session_state.messages.append({"role": "assistant", "text": response.text})
        st.rerun()

# Automatically play audio for the absolute newest message right when it arrives
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    st.write("---")
    st.write("📢 **Gemini is speaking:**")
    play_hindi_speech(st.session_state.messages[-1]["text"])
