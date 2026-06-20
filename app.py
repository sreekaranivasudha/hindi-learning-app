import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

st.set_page_config(page_title="बाल मित्र (Hindi Learner)", page_icon="🎒")
st.title("🎒 बाल मित्र - Hindi Learning Buddy")

# 1. Initialize Gemini Client (reads key from environment variables)
@st.cache_resource
def get_gemini_client():
    return genai.Client()

try:
    client = get_gemini_client()
except Exception:
    st.warning("Please configure your GEMINI_API_KEY in the sidebar or secrets.")
    client = None

# System prompt forcing Gemini to be a friendly Hindi teacher
SYSTEM_INSTRUCTION = (
    "You are a warm, encouraging, and patient scheduling and learning assistant for a child. "
    "Speak entirely in clear, friendly Hindi (Devanagari script). Keep sentences short and easy to understand. "
    "Actively praise the child to build confidence. If they upload a picture of handwriting, point out "
    "spelling/grammar errors gently and explain corrections in simple Hindi."
)

# 2. Manage Chat History
if "chat_session" not in st.session_state and client:
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Image Upload (Handwriting analysis)
st.sidebar.header("📝 Check Handwriting")
uploaded_file = st.sidebar.file_uploader("Upload handwriting picture:", type=["jpg", "jpeg", "png"])

if uploaded_file and client:
    img = Image.open(uploaded_file)
    st.sidebar.image(img, caption="Child's Writing", use_container_width=True)
    if st.sidebar.button("Analyze Writing (गलतियां सुधारें)"):
        with st.spinner("Gemini Teacher is reading..."):
            # Send image along with custom prompt to the active chat session
            response = st.session_state.chat_session.send_message(
                message=["कृपया इस लिखावट को देखें। क्या इसमें कोई वर्तनी (spelling) या व्याकरण की गलती है? मुझे प्यार से समझाएं।", img]
            )
            st.session_state.messages.append({"role": "user", "text": "📸 [Uploaded handwriting image]"})
            st.session_state.messages.append({"role": "assistant", "text": response.text})

# Main Chat Interface (Text/Voice Interaction)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["text"])

user_input = st.chat_input("Type something or paste text here...")
if user_input and client:
    st.session_state.messages.append({"role": "user", "text": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    with st.spinner("सोच रहा हूँ..."):
        response = st.session_state.chat_session.send_message(user_input)
        
    st.session_state.messages.append({"role": "assistant", "text": response.text})
    with st.chat_message("assistant"):
        st.write(response.text)
        
        # Audio playback setup using HTML5/JS Browser Text-To-Speech (Locks to Hindi voice)
        tts_html = f"""
        <script>
        var msg = new SpeechSynthesisUtterance({repr(response.text)});
        msg.lang = 'hi-IN';
        window.speechSynthesis.speak(msg);
        </script>
        """
        st.components.v1.html(tts_html, height=0)