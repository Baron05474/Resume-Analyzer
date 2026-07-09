import os
import random
import smtplib
import sqlite3
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from pypdf import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_session_key_for_resume_analyzer"

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# SMTP Settings
SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SENDER_EMAIL = "b11287001@smtp-brevo.com"
SENDER_PASSWORD = os.getenv("PROVIDER_PASSWORD")
TEMP_OTP_STORE = {}

# Database Setup
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Function for sending otp
def send_otp_email(receiver_email, name, otp):
    try:
        email_content = f"Hello {name}, your OTP is: {otp}"
        msg = MIMEText(email_content)
        msg["Subject"] = "Verify Your Account - Resume Analyzer"
        msg["From"] = "project.verify.ai@gmail.com"
        msg["To"] = receiver_email
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"CRITICAL SMTP ERROR: {e}")
        return False

# Routes
@app.route("/")
def home():
    return render_template("landing.html")

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    
    if not name or not email or not password:
        return jsonify({"message": "Please fill in all fields."}), 400

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"message": "Email already registered."}), 400
    conn.close()

    otp = str(random.randint(1000, 9999))
    TEMP_OTP_STORE[email] = {"name": name, "password": password, "otp": otp}
    
    if send_otp_email(email, name, otp):
        return jsonify({"message": "OTP sent to email.", "otp_mode": "email"}), 200
    else:
        return jsonify({"message": "Email failed.", "otp_mode": "web", "otp": otp}), 200

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    user_otp, email = data.get("otp"), data.get("email")
    temp_user = TEMP_OTP_STORE.get(email)

    if temp_user and user_otp == temp_user['otp']:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                       (temp_user['name'], email, temp_user['password']))
        conn.commit()
        conn.close()
        TEMP_OTP_STORE.pop(email, None)
        return jsonify({"message": "Account Created Successfully!"}), 200
    return jsonify({"message": "Invalid OTP."}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email, password = data.get("email"), data.get("password")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_email'] = user[2]
        session['user_name'] = user[1]
        return jsonify({"message": "Login Successful", "name": user[1]}), 200
    return jsonify({"message": "Incorrect email or password."}), 401

@app.route("/analyze", methods=["POST"])
def analyze():
    if "user_email" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    file = request.files.get("resume")
    if file and file.filename.endswith(".pdf"):
        reader = PdfReader(file)
        resume_text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        
        prompt = f"Analyze this resume: {resume_text}"
        response = model.generate_content(prompt)
        return jsonify({"message": "Success", "analysis": response.text})
    return jsonify({"message": "Invalid file."}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True) 