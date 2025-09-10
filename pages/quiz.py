import streamlit as st
import json
import re
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="DigiMent Quiz Terminal", page_icon="🧠")
st.title("🚨 DigiMent Quiz Terminal")
st.caption("May Jesus guide you :)")

page = st.selectbox("Warp to...", ["-- Select --", "Upload", "Podcast", "Pomodoro"])
if page == "Podcast":
    st.switch_page("pages/podcastifier.py")
elif page == "Upload":
    st.switch_page("digiment.py")
elif page == "Pomodoro":
    st.switch_page("pages/pomodigi.py")

# startup
if 'raw_text' not in st.session_state:
    st.session_state.raw_text = ""
if 'selected_difficulty' not in st.session_state:
    st.session_state.selected_difficulty = "easy"
if 'data' not in st.session_state:
    st.session_state.data = []
if 'show_quiz' not in st.session_state:
    st.session_state.show_quiz = False
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = []

# PROMPT JGN DIGANTI PLS
def generate_questions(text, difficulty="easy"):
    try:
        prompt = f"""
You are a quiz generator. Based on the input text, generate a JSON array of multiple-choice quiz questions.

Rules:
- Return ONLY a valid JSON array: [{{"question": "...", "options": ["Option1", "Option2", ...], "answer": "A"}}]
- Do NOT include any explanations, markdown, or additional text
- Format options as a list of strings WITHOUT LETTER PREFIXES
- The 'answer' field must be the LETTER of the correct option (A, B, C, etc.)

Difficulty settings:
- easy: 3 EASY questions
- medium: 4 MEDIUM questions
- hard: 5 HARD questions

Text:
{text}

ONLY return the JSON array.
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a strict quiz generator. Return ONLY valid JSON that follows all rules."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )

        output_text = response.choices[0].message.content.strip()
        if output_text.startswith("```"):
            output_text = re.sub(r"^```(?:json)?|```$", "", output_text, flags=re.MULTILINE).strip()

        if output_text.startswith('{'):
            data = json.loads(output_text)
            questions = data.get('questions', []) or data.get('quiz', [])
        else:
            questions = json.loads(output_text)

        return questions

    except Exception as e:
        st.error(f"Failed to generate quiz: {e}")
        return []

if not st.session_state.get("raw_text"):
    st.warning("Please upload a note file first in the 'Upload' page.")
    st.stop()

difficulty = st.radio("Choose Difficulty", ["easy", "medium", "hard"], index=["easy", "medium", "hard"].index(st.session_state.selected_difficulty))

st.session_state.selected_difficulty = difficulty
col1, col2 = st.columns(2)

with col1:
    if st.button("Generate Quiz", use_container_width=True):
        with st.spinner("Generating questions..."):
            questions = generate_questions(st.session_state.raw_text, difficulty=difficulty)
            if questions:
                st.session_state.data = questions
                st.session_state.show_quiz = True
                st.session_state.quiz_submitted = False
                st.session_state.user_answers = [None] * len(questions)

with col2:
    if st.button("Redo Quiz", use_container_width=True, disabled=not st.session_state.get("data")):
        st.session_state.quiz_submitted = False
        st.session_state.user_answers = [None] * len(st.session_state.data)
        st.success("Answers cleared.")

if st.session_state.get("show_quiz", False) and "data" in st.session_state:
    st.divider()
    st.subheader(f"{st.session_state.selected_difficulty.capitalize()} Quiz")

    with st.form("quiz_form"):
        for idx, q in enumerate(st.session_state.data):
            st.markdown(f"**Q{idx+1}: {q['question']}**")
            option_letters = [chr(65 + i) for i in range(len(q['options']))]
            labeled_options = [f"{letter}. {text}" for letter, text in zip(option_letters, q['options'])]
            current_index = None

            if st.session_state.user_answers[idx]:
                current_index = labeled_options.index(st.session_state.user_answers[idx])
            answer = st.radio(
                label=f"Select answer for Q{idx+1}:",
                options=labeled_options,
                index=current_index,
                key=f"q_{idx}"
            )
            st.session_state.user_answers[idx] = answer

        submitted = st.form_submit_button("Submit Answers", use_container_width=True)

    if submitted:
        st.session_state.quiz_submitted = True
        score = 0
        results = []
        st.divider()
        st.subheader("Results")

        for idx, q in enumerate(st.session_state.data):
            user_ans = st.session_state.user_answers[idx]
            user_letter = user_ans.split(".")[0].strip() if user_ans else "No answer"
            correct_letter = q["answer"]
            option_letters = [chr(65 + i) for i in range(len(q['options']))]
            labeled_options = [f"{letter}. {text}" for letter, text in zip(option_letters, q['options'])]

            if user_letter == correct_letter:
                score += 1
                results.append(f"✅ **Q{idx+1}:** Correct! Your answer: {user_ans}")
            else:
                correct_full = next((opt for opt in labeled_options if opt.startswith(correct_letter + ".")), "Unknown")
                results.append(f"❌ **Q{idx+1}:** Incorrect. Your answer: {user_ans or 'None'} | Correct: {correct_full}")

        for result in results:
            st.markdown(result)

        st.markdown(f"### Score: `{score} / {len(st.session_state.data)}`")

        total = len(st.session_state.data)

        if score == total:
            st.balloons()
            st.success("Perfect score! 🏆")
            st.markdown("> **Philippians 4:13** — *\"I can do all things through Christ who strengthens me.\"*")
        elif score / total >= 0.7:
            st.success("Great job!")
            st.markdown("> **Proverbs 3:5** — *\"Trust in the Lord with all your heart and lean not on your own understanding.\"*")
        elif score / total < 0.7 and score / total >= 0:
            st.warning("Keep practicing! Redo the quiz to get a better grasp on the material!!")
            st.markdown("> **Isaiah 40:31** — *\"But those who hope in the Lord will renew their strength.\"*")
        else:
            st.warning("Wow...... That's crazy...")
            st.markdown("> **Proverbs 24:16** — *\"Though the righteous fall seven times, they rise again.\"*")


#CSCSCSCSS
st.markdown("""
<style>
html, body {
    background-color: #0f0f1c;
    color: #e0e0ff;
}
.stRadio > div {
    flex-direction: row !important;
    gap: 15px;
}
.stRadio [role="radiogroup"] {
    gap: 10px;
}
.stButton button {
    width: 100%;
    transition: all 0.2s;
}
.stButton button:hover {
    transform: scale(1.04);
}
</style>
""", unsafe_allow_html=True)
