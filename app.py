import streamlit as st
from tool import setup_knowledge_base, get_questions_for_role, get_feedback, KNOWLEDGE_BASE
import asyncio

asyncio.set_event_loop(asyncio.new_event_loop())

st.set_page_config(
    page_title="Employee Appraisal Test",
    page_icon="📝",
    layout="centered"
)

if 'test_started' not in st.session_state:
    st.session_state.test_started = False
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'feedback' not in st.session_state:
    st.session_state.feedback = ""

@st.cache_resource
def load_kb():
    return setup_knowledge_base()

vector_store = load_kb()

st.title("📝 Employee Appraisal Test")
st.markdown("This test will assess your skills for your role. Please choose your role to begin.")

if not st.session_state.test_started:
    roles = list(KNOWLEDGE_BASE.keys())
    selected_role = st.selectbox("Select your Role:", options=roles)

    if st.button("Start Test", type="primary"):
        with st.spinner("Preparing your test..."):
            questions = get_questions_for_role(vector_store, selected_role, 10)
            
            if not questions:
                st.error(f"Sorry, no questions could be found for the role '{selected_role}'. Please check the knowledge_base.json file.")
            else:
                if len(questions) < 10:
                    st.warning(f"Warning: Only found {len(questions)} questions for '{selected_role}'. The test will be shorter than expected.")
                
                st.session_state.questions = questions
                st.session_state.selected_role = selected_role
                st.session_state.current_question = 0
                st.session_state.user_answers = {}
                st.session_state.score = 0
                st.session_state.feedback = ""
                st.session_state.test_started = True
                st.rerun()

elif st.session_state.current_question < len(st.session_state.questions):
    q_index = st.session_state.current_question
    question_data = st.session_state.questions[q_index]

    st.header(f"Question {q_index + 1} / {len(st.session_state.questions)}")
    st.markdown(f"**{question_data['question']}**")

    user_choice = st.radio(
        "Choose one option:",
        options=question_data['options'],
        index=None,
        key=f"q_{q_index}"
    )

    if user_choice:
        st.session_state.user_answers[q_index] = user_choice
    
    col1, col2, col3 = st.columns([1, 1, 1])
    if q_index > 0:
        if col1.button("⬅️ Previous"):
            st.session_state.current_question -= 1
            st.rerun()

    if q_index < len(st.session_state.questions) - 1:
        if col3.button("Next ➡️"):
            st.session_state.current_question += 1
            st.rerun()
    else:
        if col3.button("✅ Submit Test", type="primary"):
            st.session_state.current_question += 1
            st.rerun()

else:
    st.header("Test Completed! 🎉")
    # Calculate score only once
    if st.session_state.score == 0 and st.session_state.user_answers:
        score = 0
        for i, q in enumerate(st.session_state.questions):
            if st.session_state.user_answers.get(i) == q['answer']:
                score += 1
        st.session_state.score = score
        
    total = len(st.session_state.questions)
    st.metric(label="Your Score", value=f"{st.session_state.score}/{total}")

    if not st.session_state.feedback:
        with st.spinner("Generating your personalized feedback..."):
            st.session_state.feedback = get_feedback(
                st.session_state.score,
                total,
                st.session_state.selected_role
            )
    
    st.subheader("Personalized Feedback")
    st.info(st.session_state.feedback)

    if st.button("Restart Test"):
        st.session_state.test_started = False
        st.rerun()