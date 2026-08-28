import streamlit as st
import pickle
import pandas as pd
from datetime import datetime, timedelta

# Load model
@st.cache_resource
def load_model():
    return pickle.load(open('clinic_model.pkl', 'rb'))

model = load_model()
LOW, HIGH = 2.0, 4.0  # adjust to your percentiles

def classify(v): return "Free" if v <= LOW else "Normal" if v <= HIGH else "Busy"

def predict(dt_str):
    dt = pd.to_datetime(dt_str)
    if not (8 <= dt.hour < 12 or 16 <= dt.hour < 22):
        raise ValueError("Outside hours")
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

def email(name, mail, dt):
    return f"""--- MOCK EMAIL ---
To: {mail}

Subject: Appointment Confirmation for {name}

Dear {name},

Your appointment on {dt.strftime('%Y-%m-%d')} at {dt.strftime('%I:%M %p').lstrip('0')} is confirmed.

Thank you.
------------------"""

st.set_page_config(page_title="Clinic Chatbot", page_icon="💬")
st.title("💬 Clinic Chatbot")
st.header("Hello, Welcome to the Clinic Chatbot")

if "step" not in st.session_state: st.session_state.step = "greeting"
if "msgs" not in st.session_state: st.session_state.msgs = []
if "data" not in st.session_state: st.session_state.data = {}

for m in st.session_state.msgs:
    with st.chat_message(m[0]): st.markdown(m[1])

def say(role, text):
    st.session_state.msgs.append((role, text))
    with st.chat_message(role): st.markdown(text)

if st.session_state.step == "greeting":
    say("assistant", "Would you like a fixed appointment, or a walk-in visit? (type 'appointment' or 'walk-in')")
    st.session_state.step = "choice"

if prompt := st.chat_input("Type here..."):
    # Normalise input: strip spaces, lower case
    cmd = prompt.strip().lower()
    say("user", prompt)   # show original user input
    step = st.session_state.step
    d = st.session_state.data

    if step == "choice":
        # Accept multiple variants
        if cmd in ["appointment", "appt"]:
            say("assistant", "Enter date & time (e.g., 2026-08-29 9:30 AM):")
            st.session_state.step = "appt_dt"
        elif cmd in ["walk-in", "walkin", "walk in"]:
            say("assistant", "Enter date & time you plan to come (e.g., 2026-08-29 9:30 AM):")
            st.session_state.step = "walk_dt"
        else:
            say("assistant", "Please type 'appointment' or 'walk-in'.")

    elif step == "appt_dt":
        try:
            dt = pd.to_datetime(prompt)   # keep original prompt for parsing
            d["dt"] = dt
            say("assistant", "Your full name?")
            st.session_state.step = "appt_name"
        except:
            say("assistant", "Invalid format. Use like '2026-08-29 9:30 AM'")
    elif step == "appt_name":
        if prompt.strip():
            d["name"] = prompt.strip()
            say("assistant", "Your email?")
            st.session_state.step = "appt_email"
        else:
            say("assistant", "Name required.")
    elif step == "appt_email":
        if "@" in prompt and "." in prompt:
            d["email"] = prompt
            say("assistant", f"✅ Confirmed!\n\n{email(d['name'], d['email'], d['dt'])}")
            st.session_state.step = "done"
        else:
            say("assistant", "Invalid email.")

    elif step == "walk_dt":
        try:
            dt = pd.to_datetime(prompt)
            status = predict(dt.strftime('%Y-%m-%d %H:%M'))
            reply = f"🔍 **Prediction:** {status}\n\n"
            if status == "Busy":
                reply += "⚠️ Busy. Quieter times nearby:\n"
                sugg = suggest(dt.strftime('%Y-%m-%d %H:%M'))
                for t, s in sugg:
                    reply += f"• {t} (predicted {s})\n"
                if not sugg:
                    reply += "No alternatives – try another session."
            elif status == "Normal":
                reply += "ℹ️ It's a good time to visit."
            else:
                reply += "✅ It's a good time to visit."
            say("assistant", reply)
            st.session_state.step = "done"
        except Exception as e:
            say("assistant", f"Error: {e}. Try again.")

    elif step == "done":
        say("assistant", "Thank you! Refresh to start over.")

    st.rerun()