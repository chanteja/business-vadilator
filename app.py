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

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    user TEXT,
    idea TEXT,
    score INTEGER
)
""")
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


# ================= USER =================
if "user" not in st.session_state:
    st.session_state.user = "guest"

st.sidebar.text_input("Username", key="user")

# ================= UI =================
st.title("🚀 AI Startup Consultant")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🧪 Analyze", "⚔️ Compare", "💬 Chat", "📄 Plan", "📊 Analytics"]
)

# ================= ANALYZE =================
with tab1:
    idea = st.text_area("Enter your idea")

    if st.button("Analyze"):
        if idea:
            with st.spinner("Analyzing..."):
                result = analyze(idea)

            st.markdown(f"<div class='card'>{result}</div>", unsafe_allow_html=True)

            score = extract_score(result)
            st.progress(score / 10)

            # Save
            cursor.execute(
                "INSERT INTO history VALUES (?, ?, ?)",
                (st.session_state.user, idea, score)
            )
            conn.commit()

            # Doubt
            q = st.text_input("Ask doubt")

            if st.button("Ask AI"):
                ans = ai_response(f"Idea: {idea}\nQuestion: {q}")
                st.write(ans)

# ================= COMPARE =================
with tab2:
    i1 = st.text_area("Idea 1")
    i2 = st.text_area("Idea 2")

    if st.button("Compare"):
        try:
            r1 = analyze(i1)
            r2 = analyze(i2)
        except:
            r1 = "Fallback Score: 6/10"
            r2 = "Fallback Score: 7/10"

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
        elif s2 > s1:
            st.success("🏆 Idea 2 Wins")
        else:
            st.info("🤝 Tie")

# ================= CHAT =================
with tab3:
    if "chat" not in st.session_state:
        st.session_state.chat = []

    user_input = st.text_input("Ask startup questions")

    if st.button("Send"):
        st.session_state.chat.append(("You", user_input))
        reply = ai_response(user_input)
        st.session_state.chat.append(("AI", reply))

    for sender, msg in st.session_state.chat:
        st.write(f"**{sender}:** {msg}")

# ================= PLAN =================
with tab4:
    idea_bp = st.text_area("Enter idea for full plan")

    if st.button("Generate Plan"):
        plan = ai_response(f"Create full business plan for: {idea_bp}")
        st.write(plan)

# ================= ANALYTICS =================
with tab5:
    st.subheader("📊 Advanced Analytics")

    cursor.execute(
        "SELECT idea, score FROM history WHERE user=?",
        (st.session_state.user,)
    )
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(data, columns=["Idea", "Score"])

        st.dataframe(df)

        # Chart
        st.bar_chart(df.set_index("Idea"))

        # Avg score
        avg_score = df["Score"].mean()
        st.metric("📈 Average Score", round(avg_score, 2))

        # Best idea
        best = df.loc[df["Score"].idxmax()]
        st.success(f"🏆 Best Idea: {best['Idea']} ({best['Score']}/10)")

        # Trend
        st.line_chart(df["Score"])

        # Insights
        if avg_score > 7:
            st.success("🔥 You have strong business ideas!")
        elif avg_score > 5:
            st.warning("⚠️ Moderate ideas, refine more")
        else:
            st.error("❌ Ideas need improvement")

    else:
        st.info("No data yet")