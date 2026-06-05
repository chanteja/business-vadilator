from google import genai
import streamlit as st
import sqlite3
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

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
client = genai.Client(api_key=st.secrets["API_KEY"])

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

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text


def extract_score(text):
    match = re.search(r'(\d+)/10', text)
    return int(match.group(1)) if match else 5


# 🔐 Strong Password
def is_strong_password(password):
    return (
        len(password) >= 6 and
        any(c.isupper() for c in password) and
        any(c.islower() for c in password) and
        any(c.isdigit() for c in password)
    )


# 📄 PDF Generator
def generate_pdf(text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

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


# ================= LOGIN =================
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


# ================= AUTH UI =================
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
                st.success("✅ Login successful")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    else:
        if st.button("Signup"):
            if not is_strong_password(password):
                st.error("❌ Password must be strong (6+ chars, upper, lower, number)")
            else:
                if signup(username, password):
                    st.success("✅ Account created! Please login.")
                    st.session_state.clear()
                    st.rerun()
                else:
                    st.error("User already exists")

    st.stop()


# ================= MAIN UI =================
st.set_page_config(page_title="AI Business Validator", layout="wide")

st.title("🚀 AI Business Validator")

if st.button("Logout"):
    st.session_state.clear()
    st.rerun()

mode = st.radio("Select Mode", ["Single Idea", "Compare Ideas"])

# ================= SINGLE =================
if mode == "Single Idea":
    idea = st.text_area("💡 Enter your business idea")

    if st.button("🔍 Analyze"):
        if idea:
            try:
                st.warning("⏳ Please wait while AI analyzes your idea...")
                
                with st.spinner("🤖 Generating response..."):
                    result = analyze_business_idea(idea)

                st.success("✅ Analysis Complete")
                st.write(result)

                score = extract_score(result)
                st.progress(score / 10)

                # Save to DB
                cursor.execute(
                    "INSERT INTO history VALUES (?, ?, ?, ?)",
                    (st.session_state.username, idea, score, result)
                )
                conn.commit()

                # 📄 PDF Download
                pdf = generate_pdf(result)
                st.download_button(
                    "📄 Download PDF",
                    pdf,
                    file_name="analysis.pdf",
                    mime="application/pdf"
                )

            except:
                st.error("⚠️ API quota exceeded. Try later.")


# ================= COMPARE =================
else:
    idea1 = st.text_area("Idea 1")
    idea2 = st.text_area("Idea 2")

    if st.button("⚔️ Compare"):
        if idea1 and idea2:
            try:
                with st.spinner("Comparing ideas..."):
                    res1 = analyze_business_idea(idea1)
                    res2 = analyze_business_idea(idea2)

                score1 = extract_score(res1)
                score2 = extract_score(res2)

                st.write("### 🥇 Idea 1", res1)
                st.progress(score1 / 10)

                st.write("### 🥈 Idea 2", res2)
                st.progress(score2 / 10)

            except:
                st.error("⚠️ API error")


# ================= HISTORY =================
st.markdown("## 🧠 Your History")

cursor.execute(
    "SELECT idea, score FROM history WHERE username=?",
    (st.session_state.username,)
)

data = cursor.fetchall()

if data:
    import pandas as pd
    df = pd.DataFrame(data, columns=["Idea", "Score"])
    st.dataframe(df)
    st.line_chart(df["Score"])
else:
    st.info("No history yet")