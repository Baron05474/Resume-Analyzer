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
model = genai.GenerativeModel("models/gemini-2.5-flash")
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

# ৩. Login

@app.route("/login", methods=["POST"])

def login():

    data = request.json

    email = data.get("email")

    password = data.get("password")



    conn = sqlite3.connect("users.db")

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))

    user = cursor.fetchone()

    conn.close()



    if user:

        session['user_email'] = user[2]

        session['user_name'] = user[1]

        return jsonify({

            "message": "Login Successful",

            "name": user[1]

        }), 200

   

    return jsonify({"message": "Incorrect email or password."}), 401



# ৪. Logout

@app.route("/logout")

def logout():

    session.clear()

    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect(url_for("home"))
    return render_template("dashboard.html")



# ৫. AI Check

@app.route("/analyze", methods=["POST"])
def analyze():
    if "user_email" not in session:
        return jsonify({"message": "Unauthorized access! Please log in."}), 401

    if "resume" not in request.files:
        return jsonify({"message": "No file found."}), 400

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({"message": "No file selected"}), 400

    # ফাইল টাইপ চেক
    if file and file.filename.lower().endswith(".pdf"):
        try:
            # নিশ্চিত করো যে তুমি PyPDF2 থেকে PdfReader ইমপোর্ট করেছ
            reader = PdfReader(file)
            resume_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    resume_text += text

            if not resume_text.strip():
                return jsonify({"message": "No text could be extracted."}), 400

            # Gemini API call
            prompt = f"Analyze this resume carefully. Provide an ATS Score out of 100, brief feedback, strengths, and improvement areas. Resume text:\n\n{resume_text}"
            
            response = model.generate_content(prompt)
            analysis_result = response.text
            
            return jsonify({"message": "Success", "analysis": analysis_result})

        except Exception as e:
            return jsonify({"message": f"File Processing Error: {str(e)}"}), 500
    
    
    return jsonify({"message": "Only PDF files are allowed."}), 400



if __name__ == "__main__":

        import os

        port = int(os.environ.get("PORT", 5000))

        app.run(host="0.0.0.0")