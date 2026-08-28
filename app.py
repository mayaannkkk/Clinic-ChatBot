import streamlit as st
import pickle
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import difflib
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env (used for local dev fallback)
load_dotenv(override=True)

# ---------- Secret loading (Streamlit secrets first, then .env) ----------
def get_secret(key):
    """
    Look up a secret first in st.secrets (Streamlit Cloud / .streamlit/secrets.toml),
    then fall back to environment variables (.env for local dev).
    """
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.environ.get(key)

# ---------- Email validation ----------
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def is_valid_email(addr: str) -> bool:
    return bool(EMAIL_RE.match(addr.strip()))

# ---------- Email sender (real SMTP) ----------
def send_real_email(to_email, name, date_str, time_str):
    """
    Send a real email using Gmail SMTP with SSL context.
    Returns (success, message).
    """
    sender = get_secret("EMAIL_SENDER")
    password = get_secret("EMAIL_PASSWORD")
    if not sender or not password:
        return False, "Email credentials not set. Please set EMAIL_SENDER and EMAIL_PASSWORD in .env or Streamlit secrets."

    subject = f"Appointment Confirmation for {name}"
    body = f"""Dear {name},

Your appointment on {date_str} at {time_str} is confirmed.

Thank you for choosing our clinic.
"""

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Use SSL context (same as test_email.py)
        context = ssl.create_default_context()
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully."
    except Exception as e:
        return False, f"SMTP error: {str(e)}"

# ---------- Mock email (fallback) ----------
def mock_email(name, mail, date_str, time_str):
    return f"""--- MOCK EMAIL (real email not sent) ---
To: {mail}

Subject: Appointment Confirmation for {name}

Dear {name},

Your appointment on {date_str} at {time_str} is confirmed.

Thank you for choosing our clinic.
------------------"""

# ---------- Load model ----------
@st.cache_resource
def load_model():
    return pickle.load(open('clinic_model.pkl', 'rb'))

model = load_model()
LOW, HIGH = 2.0, 4.0  # adjust to your percentiles

def classify(v):
    return "Free" if v <= LOW else "Normal" if v <= HIGH else "Busy"

def predict(dt_str):
    dt = pd.to_datetime(dt_str)
    if not (8 <= dt.hour < 12 or 16 <= dt.hour < 22):
        raise ValueError("Outside clinic hours (8-12 AM, 4-10 PM).")
    df = pd.DataFrame([{'Date': dt.strftime('%Y-%m-%d'), 'Visit Time': dt.strftime('%I:%M %p').lstrip('0')}])
    return classify(model.predict(df)[0])

def suggest(dt_str):
    dt = pd.to_datetime(dt_str)
    times = []
    for off in [-60, -30, 30, 60]:
        nd = dt + timedelta(minutes=off)
        if 8 <= nd.hour < 22 and (8 <= nd.hour < 12 or 16 <= nd.hour < 22):
            t = nd.strftime('%I:%M %p').lstrip('0')
            times.append((t, predict(nd.strftime('%Y-%m-%d %H:%M'))))
    good = [t for t in times if t[1] != "Busy"]
    return good[:2] if good else times[:2]

# ---------- Intent classification (typo-tolerant) ----------
APPT_KEYWORDS = ["appointment", "book", "booking", "schedule", "reserve", "reservation", "appt", "fixed"]
WALK_KEYWORDS = ["walk", "walkin", "walk-in", "visit", "direct", "directly", "come", "coming", "drop", "show"]
RESTART_KEYWORDS = ["restart", "reset", "start over", "startover", "begin again", "new appointment"]

def _fuzzy_contains(word: str, keywords: list, cutoff: float = 0.78) -> bool:
    """True if `word` closely matches (or contains/is contained by) any keyword,
    tolerating small typos like missing/swapped letters."""
    if any(kw in word or word in kw for kw in keywords if len(word) >= 3):
        return True
    return bool(difflib.get_close_matches(word, keywords, n=1, cutoff=cutoff))

def classify_intent(text: str):
    text = text.lower().strip()
    words = re.findall(r"[a-z\-]+", text)

    # Exact substring check first (fast path, no false positives)
    if any(kw in text for kw in APPT_KEYWORDS):
        return "appointment"
    if any(kw in text for kw in WALK_KEYWORDS):
        return "walk-in"

    # Fuzzy fallback for typos, e.g. "wnat" -> "want" isn't a keyword itself,
    # but this catches things like "visti", "boook", "shedule", etc.
    for w in words:
        if len(w) < 3:
            continue
        if _fuzzy_contains(w, APPT_KEYWORDS):
            return "appointment"
        if _fuzzy_contains(w, WALK_KEYWORDS):
            return "walk-in"
    return None

def is_restart_request(text: str) -> bool:
    text = text.lower().strip()
    return any(kw in text for kw in RESTART_KEYWORDS)

def reset_conversation():
    st.session_state.step = "greeting"
    st.session_state.msgs = []
    st.session_state.data = {}

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Clinic Chatbot", page_icon="💬")
st.title("💬 Clinic Chatbot")
st.header("Hello, Welcome to the Clinic Chatbot")

if "step" not in st.session_state:
    st.session_state.step = "greeting"
if "msgs" not in st.session_state:
    st.session_state.msgs = []
if "data" not in st.session_state:
    st.session_state.data = {}

for m in st.session_state.msgs:
    with st.chat_message(m[0]):
        st.markdown(m[1])

if st.session_state.step == "done":
    if st.button("Start Over"):
        reset_conversation()
        st.rerun()

def say(role, text):
    st.session_state.msgs.append((role, text))
    with st.chat_message(role):
        st.markdown(text)

if st.session_state.step == "greeting":
    say("assistant", "Would you like a fixed appointment, or a walk-in visit?")
    st.session_state.step = "choice"

def process_appt_datetime(dt):
    d = st.session_state.data
    if not (8 <= dt.hour < 12 or 16 <= dt.hour < 22):
        say("assistant", "That time is outside clinic hours (8:00 AM–12:00 PM and 4:00 PM–10:00 PM). Please pick a time within those windows.")
        return
    d["dt"] = dt
    d["date_str"] = dt.strftime('%Y-%m-%d')
    d["time_str"] = dt.strftime('%I:%M %p').lstrip('0')
    say("assistant", "Your full name?")
    st.session_state.step = "appt_name"

def process_walk_datetime(dt):
    try:
        status = predict(dt.strftime('%Y-%m-%d %H:%M'))
        reply = f"**Prediction:** {status}\n\n"
        if status == "Busy":
            reply += "Busy. Quieter times nearby:\n"
            sugg = suggest(dt.strftime('%Y-%m-%d %H:%M'))
            for t, s in sugg:
                reply += f"• {t} (predicted {s})\n"
            if not sugg:
                reply += "No alternatives – try another session."
        elif status == "Normal":
            reply += "It's a good time to visit."
        else:
            reply += "It's a good time to visit."
        say("assistant", reply)
        st.session_state.step = "done"
    except Exception as e:
        say("assistant", f"Error: {e}. Try again.")

def datetime_picker(key_prefix, on_confirm):
    """Reliable date/time picker so users never have to type a date string."""
    with st.form(key=f"{key_prefix}_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            picked_date = st.date_input("Date", value=datetime.now().date(), key=f"{key_prefix}_date")
        with c2:
            picked_time = st.time_input("Time", value=datetime.now().time().replace(second=0, microsecond=0), key=f"{key_prefix}_time")
        submitted = st.form_submit_button("Confirm date & time")
    if submitted:
        dt = datetime.combine(picked_date, picked_time)
        on_confirm(dt)
        st.rerun()

if st.session_state.step == "appt_dt":
    datetime_picker("appt", process_appt_datetime)
elif st.session_state.step == "walk_dt":
    datetime_picker("walk", process_walk_datetime)

if prompt := st.chat_input("Type here..."):
    say("user", prompt)

    if is_restart_request(prompt):
        reset_conversation()
        st.rerun()

    step = st.session_state.step
    d = st.session_state.data

    if step == "choice":
        intent = classify_intent(prompt)
        if intent == "appointment":
            say("assistant", "Great — please pick your appointment date & time using the picker below.")
            st.session_state.step = "appt_dt"
        elif intent == "walk-in":
            say("assistant", "Great — please pick the date & time you plan to come using the picker below.")
            st.session_state.step = "walk_dt"
        else:
            say("assistant", "I didn't understand. Would to like to book an appointment or want to visit as a walk-in?")

    elif step == "appt_dt":
        say("assistant", "Please use the date & time picker above (or below the chat) instead of typing — it avoids formatting errors.")

    elif step == "appt_name":
        if prompt.strip():
            d["name"] = prompt.strip()
            say("assistant", "Your email?")
            st.session_state.step = "appt_email"
        else:
            say("assistant", "Name required.")

    elif step == "appt_email":
        email_addr = prompt.strip()
        if is_valid_email(email_addr):
            d["email"] = email_addr
            # Try to send real email
            success, msg = send_real_email(
                email_addr,
                d["name"],
                d["date_str"],
                d["time_str"]
            )
            if success:
                st.success("Real email sent to " + email_addr)
                say("assistant", f"Appointment confirmed! A confirmation email has been sent to {email_addr}.")
            else:
                # Show the exact error in red
                st.error(f"Email error: {msg}")
                # Fallback to mock email
                say("assistant", f"Could not send real email. Showing mock instead.\n\n{mock_email(d['name'], email_addr, d['date_str'], d['time_str'])}")
            st.session_state.step = "done"
        else:
            say("assistant", "That doesn't look like a valid email address. Please enter it like name@example.com")

    elif step == "walk_dt":
        try:
            dt = pd.to_datetime(prompt)
            status = predict(dt.strftime('%Y-%m-%d %H:%M'))
            reply = f"**Prediction:** {status}\n\n"
            if status == "Busy":
                reply += "Busy. Quieter times nearby:\n"
                sugg = suggest(dt.strftime('%Y-%m-%d %H:%M'))
                for t, s in sugg:
                    reply += f"• {t} (predicted {s})\n"
                if not sugg:
                    reply += "No alternatives – try another session."
            elif status == "Normal":
                reply += "It's a good time to visit."
            else:
                reply += "It's a good time to visit."
            say("assistant", reply)
            st.session_state.step = "done"
        except Exception as e:
            say("assistant", f"Error: {e}. Try again.")

    elif step == "done":
        say("assistant", "Thank you! Click 'Start Over' below (or type 'start over') to begin a new conversation.")

    st.rerun()