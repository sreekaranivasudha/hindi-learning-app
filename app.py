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

SYSTEM_INSTRUCTION = (
    "You are a warm, encouraging, and patient scheduling and learning assistant for a child. "
    "Speak entirely in clear, friendly Hindi (Devanagari script). Keep sentences short and easy to understand. "
    "Actively praise the child to build confidence. If they upload a picture of handwriting, point out "
    "spelling/grammar errors gently and explain corrections in simple Hindi."
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

# --- SIDEBAR: INTERFACE FOR HANDWRITING AND PATTERNS ---
st.sidebar.header("📝 2. Check Handwriting")
st.sidebar.write("Upload a picture of your Hindi writing here!")
uploaded_file = st.sidebar.file_uploader("Choose a photo...", type=["jpg", "jpeg", "png"])

if uploaded_file and client:
    img = Image.open(uploaded_file)
    st.sidebar.image(img, caption="Your Writing", use_container_width=True)
    if st.sidebar.button("Analyze My Writing (गलतियां सुधारें)"):
        with st.spinner("Gemini Teacher is analyzing your writing..."):
            response = st.session_state.chat_session.send_message(
                message=["कृपया इस लिखावट को देखें। बच्चे ने क्या लिखा है उसे बताएं और अगर कोई व्याकरण या वर्तनी की गलती है तो प्यार से सुधारें।", img]
            )
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
        response = st.session_state.chat_session.send_message(
            message=[
                "Listen to this audio clip from the child. It is in Hindi. Reply to them warmly in friendly Hindi text.",
                {"data": audio_bytes, "mime_type": "audio/wav"}
            ]
        )
        st.session_state.messages.append({"role": "user", "text": "🎤 [Sent a voice message]"})
        st.session_state.messages.append({"role": "assistant", "text": response.text})
        st.rerun()

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