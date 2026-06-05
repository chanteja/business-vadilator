from groq import Groq
import streamlit as st
import sqlite3
import re
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# ================= CONFIG =================
st.set_page_config(page_title="AI Business Validator", layout="wide")

# ================= CSS =================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0f172a, #1e293b);
}
.stButton>button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    font-weight: bold;
}
.card {
    padding: 20px;
    border-radius: 15px;
    background: #1e293b;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# ================= DATABASE =================
conn = sqlite3.connect("app.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    username TEXT,
    idea TEXT,
    score INTEGER,
    result TEXT
)
""")

conn.commit()

# ================= API =================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ================= FUNCTIONS =================
def analyze_business_idea(idea):
    prompt = f"""
    Analyze this business idea:

    {idea}

    Give:
    - Refined Idea
    - Target Audience
    - Market Analysis
    - Competitors
    - Revenue Model
    - SWOT Analysis
    - Feasibility Score (out of 10)
    - Final Verdict
    """

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def extract_score(text):
    match = re.search(r'(\d+)/10', text)
    return int(match.group(1)) if match else 5


def is_strong_password(password):
    return (
        len(password) >= 6 and
        any(c.isupper() for c in password) and
        any(c.islower() for c in password) and
        any(c.isdigit() for c in password)
    )


def generate_pdf(text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "AI Business Analysis Report")

    c.setFont("Helvetica", 10)

    y = 750
    for line in text.split("\n"):
        c.drawString(50, y, line[:90])
        y -= 15
        if y < 50:
            c.showPage()
            y = 750

    c.save()
    buffer.seek(0)
    return buffer


# ================= AUTH =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login(username, password):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return cursor.fetchone()

def signup(username, password):
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except:
        return False


# ================= LOGIN UI =================
if not st.session_state.logged_in:
    st.title("🔐 Login / Signup")

    option = st.radio("Select", ["Login", "Signup"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Login":
        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("🚀 Welcome " + username)
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    else:
        if st.button("Signup"):
            if not is_strong_password(password):
                st.error("❌ Weak password")
            else:
                if signup(username, password):
                    st.success("✅ Account created. Login now")
                    st.session_state.clear()
                    st.rerun()
                else:
                    st.error("User exists")

    st.stop()


# ================= MAIN UI =================
st.title("🚀 AI Business Validator")
st.caption("Turn Ideas into Startups | Powered by Groq ⚡")

if st.button("Logout"):
    st.session_state.clear()
    st.rerun()

mode = st.radio("Select Mode", ["Single Idea", "Compare Ideas"])

# ================= SINGLE =================
if mode == "Single Idea":
    idea = st.text_area(
        "💡 Enter your business idea",
        placeholder="Example: AI-based food delivery app"
    )

    if st.button("🔍 Analyze"):
        if idea:
            try:
                st.warning("⏳ AI is thinking...")

                with st.spinner("Generating insights..."):
                    result = analyze_business_idea(idea)

            except:
                st.error("⚠️ AI busy, showing demo result")
                result = """
                - Target: Students
                - Market: Growing
                - Revenue: Subscription
                - Feasibility Score: 7/10
                """

            st.success("✅ Analysis Ready")

            st.markdown("### 📊 Analysis")
            st.markdown(f"<div class='card'>{result}</div>", unsafe_allow_html=True)

            score = extract_score(result)

            st.markdown("### ⭐ Score")
            st.progress(score / 10)

            if score >= 8:
                st.success("🔥 Excellent Idea")
            elif score >= 5:
                st.warning("⚠️ Moderate")
            else:
                st.error("❌ Improve it")

            # Save history
            cursor.execute(
                "INSERT INTO history VALUES (?, ?, ?, ?)",
                (st.session_state.username, idea, score, result)
            )
            conn.commit()

            # PDF
            pdf = generate_pdf(result)
            st.download_button("📄 Download PDF", pdf, "report.pdf")


# ================= COMPARE =================
else:
    idea1 = st.text_area("Idea 1")
    idea2 = st.text_area("Idea 2")

    if st.button("⚔️ Compare"):
        if idea1 and idea2:
            try:
                with st.spinner("Comparing..."):
                    res1 = analyze_business_idea(idea1)
                    res2 = analyze_business_idea(idea2)
            except:
                st.error("⚠️ AI issue")

            score1 = extract_score(res1)
            score2 = extract_score(res2)

            st.write("### 🥇 Idea 1")
            st.write(res1)
            st.progress(score1 / 10)

            st.write("### 🥈 Idea 2")
            st.write(res2)
            st.progress(score2 / 10)

            if score1 > score2:
                st.success("🏆 Idea 1 Wins")
            elif score2 > score1:
                st.success("🏆 Idea 2 Wins")
            else:
                st.info("🤝 Tie")


# ================= HISTORY =================
st.markdown("## 🧠 Your History")

cursor.execute(
    "SELECT idea, score FROM history WHERE username=?",
    (st.session_state.username,)
)

data = cursor.fetchall()

if data:
    df = pd.DataFrame(data, columns=["Idea", "Score"])
    st.dataframe(df)
    st.bar_chart(df.set_index("Idea"))
else:
    st.info("No history yet")