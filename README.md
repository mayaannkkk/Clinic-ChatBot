🏥 Clinic Chatbot
Overview

A simple clinic chatbot built using Streamlit and Scikit-Learn.

The chatbot helps patients:

Book a fixed appointment
Check clinic busyness for a walk-in visit

For walk-in visits, a trained machine learning model predicts whether the clinic is likely to be Busy, Normal, or Free based on the selected date and time.

Architecture
Streamlit UI
      │
      ▼
Chatbot
(Greet Patient)
      │
      ▼
─────────────────────────────
│                           │
▼                           ▼

Appointment            Walk-In Visit

│                       │
▼                       ▼

Ask Name               Ask Date & Time
Ask Date & Time             │
Ask Email                   ▼
│                     ML Model Prediction
▼                           │
Send Confirmation           ▼
(Mock Email)         ┌───────────────┐
                     │ Busy          │
                     │ Normal / Free │
                     └───────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼

         Suggest 1–2          Confirm Good
       Alternative Times          Time
How the Chatbot Uses the ML Model
Appointment Path
User selects Appointment
Chatbot collects:
Name
Date & Time
Email
Appointment is confirmed.
A mock confirmation email is displayed.
Walk-In Path
User selects Walk-In Visit
Chatbot asks for the planned visit date and time.
The chatbot sends the date and time to the trained ML model.
The model predicts the expected clinic load.
The prediction is classified as:
Busy
Normal
Free
If Busy, the chatbot suggests 1–2 nearby quieter time slots.
Otherwise, the chatbot confirms it is a good time to visit.
Project Structure
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
How to Run
Install Dependencies
pip install -r requirements.txt
Run the Application
streamlit run app.py

Open the browser and interact with the chatbot.

Technologies Used
Streamlit
Pandas
NumPy
Scikit-Learn
Pickle

This project demonstrates how a machine learning model can be integrated into a conversational clinic assistant to help patients choose less crowded walk-in visit times.