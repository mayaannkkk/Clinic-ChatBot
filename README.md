# 🏥 Clinic Chatbot

## Overview

A simple clinic chatbot built using Streamlit and Scikit-Learn.

The chatbot allows patients to:

- Book a fixed appointment
- Check clinic busyness for a walk-in visit

For walk-in visits, a trained machine learning model predicts whether the clinic is likely to be **Free**, **Normal**, or **Busy** based on the selected date and time.

If the selected time is busy, the chatbot suggests 1–2 nearby quieter time slots.

---

## Architecture

```text
Streamlit UI
      │
      ▼
Chatbot
(Greet Patient)
      │
      ▼
 ┌──────────────┴──────────────┐
 │                             │
 ▼                             ▼

Appointment              Walk-In Visit

 │                             │
 ▼                             ▼

Collect Name         Collect Date & Time
Collect Date/Time            │
Collect Email                ▼
 │                     ML Model Prediction
 ▼                             │
Send Confirmation             ▼
(Mock Email)         Busy / Normal / Free
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼

            Suggest Alternatives   Confirm Good Time
```

---

## How the Chatbot Uses the ML Model

### Appointment Path
- Collects name, date/time, and email.
- Confirms the appointment.
- Displays a mock confirmation email.

### Walk-In Path
- Collects the planned visit date and time.
- Sends the information to the trained ML model.
- The model predicts the expected clinic load.
- Returns:
  - Free
  - Normal
  - Busy
- If Busy, the chatbot suggests nearby quieter time slots.

---

## Project Structure

```text
Clinic-Chatbot/
│
├── app.py
├── clinic_model.pkl
├── clinic_visits.csv
├── feature_engineering.py
├── ml_model.ipynb
├── predict_test.ipynb
├── requirements.txt
└── README.md
```

---

## Run the Application

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the chatbot:

```bash
streamlit run app.py
```

---

## Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- Scikit-Learn

This project demonstrates how a machine learning model can be integrated into a conversational clinic assistant to help patients choose less crowded walk-in visit times.
