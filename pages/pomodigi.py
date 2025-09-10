import streamlit as st
import time

st.set_page_config(page_title="Pomodigi Timer", page_icon="⏱️")
st.title("⏱️ Pomodigi Timer")
page = st.selectbox("Warp to...", ["-- Select --", "Upload", "Quiz", "Podcast"])
if page == "Upload":
    st.switch_page("digiment.py")
elif page == "Quiz":
    st.switch_page("pages/quiz.py")
elif page == "Podcast":
    st.switch_page("pages/podcasifier.py")

if 'pomodoro' not in st.session_state:
    st.session_state.pomodoro = {
        'running': False,
        'phase': "Work",
        'end_time': None,
        'pomodoros_completed': 0,
        'last_update': time.time()
    }

work_duration = 60 * 25 #* 60 # 25 minutes
short_break_duration = 60 * 5 #* 60  # 5 minutes
long_break_duration = 60 * 20 #* 60  # 20 minutes
pomodoros_before_long_break = 4

def update_timer():
    current_time = time.time()
    if st.session_state.pomodoro['running'] and st.session_state.pomodoro['end_time']:
        time_remaining = st.session_state.pomodoro['end_time'] - current_time
        
        if time_remaining <= 0:
            st.session_state.pomodoro['pomodoros_completed'] += 1
            
            if st.session_state.pomodoro['phase'] == "Work":
                if st.session_state.pomodoro['pomodoros_completed'] % pomodoros_before_long_break == 0:
                    st.session_state.pomodoro['phase'] = "Long Break"
                    st.session_state.pomodoro['end_time'] = current_time + long_break_duration
                else:
                    st.session_state.pomodoro['phase'] = "Short Break"
                    st.session_state.pomodoro['end_time'] = current_time + short_break_duration
            else:
                st.session_state.pomodoro['phase'] = "Work"
                st.session_state.pomodoro['end_time'] = current_time + work_duration
            
            st.session_state.pomodoro['last_update'] = current_time
            st.rerun()

def start_timer():
    st.session_state.pomodoro['running'] = True
    st.session_state.pomodoro['end_time'] = time.time() + (
        work_duration if st.session_state.pomodoro['phase'] == "Work" else
        short_break_duration if st.session_state.pomodoro['phase'] == "Short Break" else
        long_break_duration
    )
    st.session_state.pomodoro['last_update'] = time.time()

def reset_timer():
    st.session_state.pomodoro = {
        'running': False,
        'phase': "Work",
        'end_time': None,
        'pomodoros_completed': 0,
        'last_update': time.time()
    }

if 'heartbeat' not in st.session_state:
    st.session_state.heartbeat = 0

update_timer()
timer_placeholder = st.empty()
status_placeholder = st.empty()

col1, col2 = st.columns(2)
with col1:
    if st.button("Start", use_container_width=True, key="start_btn"):
        start_timer()
with col2:
    if st.button("Stop", use_container_width=True, key="reset_btn"):
        reset_timer()

if st.session_state.pomodoro['running'] and st.session_state.pomodoro['end_time']:
    time_remaining = max(0, st.session_state.pomodoro['end_time'] - time.time())
    mins, secs = divmod(int(time_remaining), 60)
    time_display = f"{mins:02d}:{secs:02d}"
    
    status_placeholder.markdown(f"### Current Phase: **{st.session_state.pomodoro['phase']}**")
    timer_placeholder.markdown(f"""
    <div style='
        font-size: 3rem;
        text-align: center;
        color: #66ccff;
        text-shadow: 0 0 10px #3b3bff;
        margin: 20px 0;
    '>
        {time_display}
    </div>
    """, unsafe_allow_html=True)
    
    # UPDATE DISPLAY
    if st.session_state.pomodoro['running']:
        time.sleep(0.1) 
        st.session_state.heartbeat += 1
        st.rerun()
else:
    status_placeholder.markdown("### Timer is **stopped**")
    timer_placeholder.markdown("""
    <div style='
        font-size: 2rem;
        text-align: center;
        color: #e0e0ff;
        margin: 20px 0;
    '>
        Ready to start
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
.stButton button {
    border: none;
    border-radius: 10px;
    font-weight: bold;
    padding: 10px 20px;
    width: 100%;
    transition: transform 0.2s ease;
}
.stButton button:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)