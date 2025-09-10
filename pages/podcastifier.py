import streamlit as st
from openai import OpenAI
import tempfile

st.set_page_config(page_title="DigiMent Podcast Studio", page_icon="🎙️")
st.title("🎙️ DigiMent Podcast Studio")
page = st.selectbox("Warp to...", ["-- Select --", "Upload", "Quiz", "Pomodoro"])
if page == "Upload":
    st.switch_page("digiment.py")
elif page == "Quiz":
    st.switch_page("pages/quiz.py")
elif page == "Pomodoro":
    st.switch_page("pages/pomodigi.py")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_podcast_script(summary_notes):
    prompt = f"""
You are a podcast scriptwriter. Convert these notes into a full podcast script with:
- Title as first line
- Catchy intro
- Main content in logical flow
- Rhetorical questions/analogies
- Closing summary
- 2-3 Q&A
- Closing statement

Podcast name: 'Digiment's Podcast'
Host name: 'Digiment AI'
Write only strictly the raw text script without fillers like [Intro]

Notes:
\"\"\"{summary_notes}\"\"\"
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You write engaging podcast scripts from study notes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def convert_script_to_audio(script_text):
    response = client.audio.speech.create(
        model="tts-1",
        input=script_text,
        voice="echo"
    )
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    response.write_to_file(temp_audio)
    return temp_audio

# Main content
if 'raw_text' not in st.session_state or not st.session_state.raw_text:
    st.warning("Please upload and extract text first in the Upload page")
    st.stop()

st.subheader("Your Extracted Content")
st.text_area("Original Text", st.session_state.raw_text, height=200, disabled=True)

if st.button("Generate Podcast"):
    with st.spinner("Creating podcast script..."):
        script = generate_podcast_script(st.session_state.raw_text)
        
    st.subheader("Podcast Script")
    st.text_area("Script", script, height=400)
    
    with st.spinner("Generating audio..."):
        audio_path = convert_script_to_audio(script)
    
    st.audio(audio_path, format="audio/mp3")
    
    st.download_button("Download Script", script, file_name="podcast_script.txt")
    with open(audio_path, "rb") as f:
        st.download_button("Download Audio", f, file_name="podcast.mp3")

# CSS styling
st.markdown("""
<style>
[data-testid="stTextArea"] textarea {
    color: #e0e0ff !important;
    background-color: #1b1b3c !important;
}
</style>
""", unsafe_allow_html=True)