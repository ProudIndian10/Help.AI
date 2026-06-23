import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import speech_to_text

# 1. Premium Dark Theme UI Config
st.set_page_config(page_title="Help.AI", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    /* Absolute Dark Core */
    .stApp { background-color: #131314; color: #e3e3e3; }
    div[data-testid="stSidebar"] { background-color: #1e1f20 !important; position: relative; }
    
    /* Layout styling for the main text input line */
    .chat-title {
        font-size: 38px; font-weight: bold;
        background: -webkit-linear-gradient(160deg, #4285f4, #a06ee1, #e91e63);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    /* Stick the bottom inputs to the page dock frame */
    div[data-testid="stVerticalBlockBorderWrapper"] > div:last-child {
        position: fixed; bottom: 0; background-color: #131314; z-index: 99; padding-bottom: 25px;
    }
    
    /* Sticky footer styling trick inside the sidebar stack */
    .sidebar-footer {
        position: absolute; bottom: 10px; width: 100%; padding-right: 20px;
        border-top: 1px solid #3c4043; padding-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Secure Gemini Model Pipeline Connection
# Replace with your actual Google AI Studio API key
# This tells the app to look for a hidden password instead of typing it out loud
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# Helper function to prompt AI to generate a precise 3-4 word title for thread histories
def generate_topic_title(first_question):
    try:
        prompt = f"Generate a brief, 3 to 4 word conversational title summarizing this exact prompt. Return only the title string, no quotes, no conversational filler: '{first_question}'"
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text.strip().replace('"', '')
    except:
        return first_question[:25] + "..."

# 3. State Engine Trackers 
if "recent_chats" not in st.session_state:
    st.session_state.recent_chats = {"New Conversation": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Conversation"
if "settings_open" not in st.session_state:
    st.session_state.settings_open = False

current_messages = st.session_state.recent_chats[st.session_state.current_chat]

# 4. SIDEBAR NAVIGATION CONTROLS
with st.sidebar:
    st.markdown("<h2 style='color: white; margin-bottom:0;'>✨ Help.AI</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Primary CTA Button
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        if "New Conversation" not in st.session_state.recent_chats:
            st.session_state.recent_chats["New Conversation"] = []
        st.session_state.current_chat = "New Conversation"
        st.rerun()
        
    st.markdown("---")
    st.markdown("<p style='color: #9aa0a6; font-size: 13px; font-weight: 500;'>Recent Conversations</p>", unsafe_allow_html=True)
    
    # Render Dynamic Context Topics list
    for chat_title in list(st.session_state.recent_chats.keys()):
        if chat_title != "New Conversation":
            is_active = (chat_title == st.session_state.current_chat)
            if st.button(f"💬 {chat_title}", key=f"nav_{chat_title}", disabled=is_active, use_container_width=True):
                st.session_state.current_chat = chat_title
                st.rerun()

    # Dynamic spacing buffer
    st.markdown("<div style='height: 35vh;'></div>", unsafe_allow_html=True)
    
    # 5. SETTINGS PANEL BUTTON (At the bottom of the sidebar)
    st.markdown("<div class='sidebar-footer'>", unsafe_allow_html=True)
    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.settings_open = not st.session_state.settings_open
    st.markdown("</div>", unsafe_allow_html=True)

# 6. SETTINGS MODAL INTERFACE TOGGLE
if st.session_state.settings_open:
    with st.expander("🛠️ Workspace Application Settings", expanded=True):
        st.subheader("Model Parameters")
        st.slider("Creativity (Temperature)", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
        st.text_area("System Prompt Directives", placeholder="You are a helpful, premium AI companion...")

# 7. MAIN HUB CONTENT ROUTER
if st.session_state.current_chat == "New Conversation" and len(current_messages) == 0:
    st.markdown("<div style='height: 12vh;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='chat-title'>Hello, What can I do for you Today?</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<h3 style='color:#e3e3e3; font-weight:400;'>{st.session_state.current_chat}</h3>", unsafe_allow_html=True)
    st.markdown("---")

# Render active layout logs
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 8. PREMIUM HORIZONTAL LOWER CHAT BLOCK DOCK
st.markdown("<div style='height: 160px;'></div>", unsafe_allow_html=True)

input_col, mic_col = st.columns([0.88, 0.12])
user_query = None
uploaded_parts = []

with input_col:
    uploaded_file = st.file_uploader("Upload reference documents", type=["png", "jpg", "jpeg", "pdf", "txt"], label_visibility="collapsed")
    if uploaded_file:
        file_bytes = uploaded_file.read()
        uploaded_parts.append(types.Part.from_bytes(data=file_bytes, mime_type=uploaded_file.type))
        st.success(f"📎 File attached: {uploaded_file.name}")

    chat_text = st.chat_input("Ask a question, analyze documents...")
    if chat_text:
        user_query = chat_text

with mic_col:
    st.markdown("<div style='padding-top: 4px;'></div>", unsafe_allow_html=True)
    # Inline microphone tool
    spoken_text = speech_to_text(start_prompt="🎤 Mic", stop_prompt="🛑 Send", key='dock_mic')
    if spoken_text:
        user_query = spoken_text

# 9. CENTRAL EXECUTION PROCESSING ENGINE
if user_query:
    st.chat_message("user").markdown(user_query)
    current_messages.append({"role": "user", "content": user_query})
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing parameters..."):
            payload = [user_query] + uploaded_parts
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=payload
            )
            st.markdown(response.text)
            current_messages.append({"role": "assistant", "content": response.text})
            
    if st.session_state.current_chat == "New Conversation":
        topic_title = generate_topic_title(user_query)
        st.session_state.recent_chats[topic_title] = st.session_state.recent_chats.pop("New Conversation")
        st.session_state.current_chat = topic_title
        st.rerun()