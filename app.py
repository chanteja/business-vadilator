from groq import Groq
import streamlit as st
import sqlite3
import pandas as pd
import re

# ================= CONFIG =================
st.set_page_config(page_title="AI Startup Consultant", layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.stButton>button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 10px;
}
.card {
    padding: 20px;
    border-radius: 15px;
    background: #1e293b;
}
</style>
""", unsafe_allow_html=True)

# ================= DB =================
conn = sqlite3.connect("app.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS history (idea TEXT, score INT)")
conn.commit()

# ================= API =================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ================= FUNCTIONS =================
def ai_response(prompt):
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def analyze(idea):
    prompt = f"""
    Analyze this business idea:

    {idea}

    Give:
    - Market
    - Target users
    - Revenue model
    - SWOT
    - Feasibility Score (out of 10)
    """
    return ai_response(prompt)


def extract_score(text):
    match = re.search(r'(\d+)/10', text)
    return int(match.group(1)) if match else 5


# ================= UI =================
st.title("🚀 AI Startup Consultant")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🧪 Analyze", "⚔️ Compare", "💬 Chat", "📄 Business Plan", "📊 History"]
)

# ================= TAB 1 =================
with tab1:
    idea = st.text_area("Enter your idea")

    if st.button("Analyze"):
        if idea:
            with st.spinner("Analyzing..."):
                result = analyze(idea)

            st.markdown(f"<div class='card'>{result}</div>", unsafe_allow_html=True)

            score = extract_score(result)
            st.progress(score / 10)

            cursor.execute("INSERT INTO history VALUES (?, ?)", (idea, score))
            conn.commit()

            # Follow-up
            q = st.text_input("Ask doubt")

            if st.button("Ask AI"):
                ans = ai_response(f"Idea: {idea}\nQuestion: {q}")
                st.write(ans)

# ================= TAB 2 =================
with tab2:
    i1 = st.text_area("Idea 1")
    i2 = st.text_area("Idea 2")

    if st.button("Compare"):
        with st.spinner("Comparing..."):
            r1 = analyze(i1)
            r2 = analyze(i2)

        s1 = extract_score(r1)
        s2 = extract_score(r2)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"<div class='card'>{r1}</div>", unsafe_allow_html=True)
            st.progress(s1 / 10)

        with col2:
            st.markdown(f"<div class='card'>{r2}</div>", unsafe_allow_html=True)
            st.progress(s2 / 10)

        if s1 > s2:
            st.success("🏆 Idea 1 Wins")
        else:
            st.success("🏆 Idea 2 Wins")

# ================= TAB 3 =================
with tab3:
    if "chat" not in st.session_state:
        st.session_state.chat = []

    user = st.text_input("Ask anything about startups")

    if st.button("Send"):
        st.session_state.chat.append(("You", user))
        reply = ai_response(user)
        st.session_state.chat.append(("AI", reply))

    for sender, msg in st.session_state.chat:
        st.write(f"**{sender}:** {msg}")

# ================= TAB 4 =================
with tab4:
    idea_bp = st.text_area("Enter idea for full business plan")

    if st.button("Generate Plan"):
        plan = ai_response(f"Create full business plan for: {idea_bp}")
        st.write(plan)

# ================= TAB 5 =================
with tab5:
    cursor.execute("SELECT * FROM history")
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(data, columns=["Idea", "Score"])
        st.dataframe(df)
        st.bar_chart(df.set_index("Idea"))