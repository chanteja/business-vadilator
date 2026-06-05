from groq import Groq
import streamlit as st
import sqlite3
import pandas as pd
import re
import time

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

# Create tables safely
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    idea TEXT,
    score INTEGER
)
""")

conn.commit()

# ================= API =================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ================= AI (UNSTOPPABLE) =================
def ai_response(prompt):

    # Try 1
    try:
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
    except:
        pass

    # Try 2
    try:
        time.sleep(1)
        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
    except:
        pass

    # Final fallback
    return """
⚠️ AI is busy. Showing sample output:

- Market: Growing  
- Target: Students  
- Revenue: Subscription  
- Feasibility Score: 7/10  
"""

# ================= FUNCTIONS =================
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

def strong_password(p):
    return len(p) >= 6 and any(c.isupper() for c in p) and any(c.isdigit() for c in p)

# ================= LOGIN =================
if "logged" not in st.session_state:
    st.session_state.logged = False

def login(u, p):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    return cursor.fetchone()

def signup(u, p):
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?)", (u, p))
        conn.commit()
        return True
    except:
        return False

# ================= AUTH UI =================
if not st.session_state.logged:

    st.title("🔐 Login / Signup")

    choice = st.radio("Select", ["Login", "Signup"])

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if choice == "Login":
        if st.button("Login"):
            if login(user, pwd):
                st.session_state.logged = True
                st.session_state.user = user
                st.success("✅ Welcome " + user)
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    else:
        if st.button("Signup"):
            if not strong_password(pwd):
                st.error("Password must contain uppercase + number")
            elif signup(user, pwd):
                st.success("Account created! Login now")
            else:
                st.error("User already exists")

    st.stop()

# ================= MAIN APP =================
st.title("🚀 AI Startup Consultant")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🧪 Analyze", "⚔️ Compare", "💬 Chat", "📄 Plan", "📊 Analytics"]
)

# ================= ANALYZE =================
with tab1:
    idea = st.text_area("Enter your idea")

    if st.button("Analyze"):
        if idea:
            st.info("🤖 AI Running...")
            result = analyze(idea)

            st.markdown(f"<div class='card'>{result}</div>", unsafe_allow_html=True)

            score = extract_score(result)
            st.progress(score / 10)

            # SAFE INSERT
            cursor.execute(
                "INSERT INTO history (user, idea, score) VALUES (?, ?, ?)",
                (st.session_state.user, idea, score)
            )
            conn.commit()

# ================= COMPARE =================
with tab2:
    i1 = st.text_area("Idea 1")
    i2 = st.text_area("Idea 2")

    if st.button("Compare"):
        r1 = analyze(i1)
        r2 = analyze(i2)

        s1 = extract_score(r1)
        s2 = extract_score(r2)

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"<div class='card'>{r1}</div>", unsafe_allow_html=True)
            st.progress(s1 / 10)

        with c2:
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

    msg = st.text_input("Ask something")

    if st.button("Send"):
        st.session_state.chat.append(("You", msg))
        reply = ai_response(msg)
        st.session_state.chat.append(("AI", reply))

    for s, m in st.session_state.chat:
        st.write(f"**{s}:** {m}")

# ================= PLAN =================
with tab4:
    idea2 = st.text_area("Enter idea for business plan")

    if st.button("Generate Plan"):
        plan = ai_response(f"Create startup plan for {idea2}")
        st.write(plan)

# ================= ANALYTICS =================
with tab5:
    cursor.execute(
        "SELECT idea, score FROM history WHERE user=?",
        (st.session_state.user,)
    )
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(data, columns=["Idea", "Score"])

        st.dataframe(df)
        st.bar_chart(df.set_index("Idea"))

        avg = df["Score"].mean()
        st.metric("Average Score", round(avg, 2))

        best = df.loc[df["Score"].idxmax()]
        st.success(f"Best Idea: {best['Idea']} ({best['Score']}/10)")
    else:
        st.info("No history yet")