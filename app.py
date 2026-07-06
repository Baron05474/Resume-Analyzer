import os
import random
import smtplib
import sqlite3
import os
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from pypdf import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = "super_secret_session_key_for_resume_analyzer"  # for safety

# Gemini API Key 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# For sending OTP to user Email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "project.verify.ai@gmail.com"        # My Email account
TEMP_OTP_STORE = {}  # for sending email 16 digit pass

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
def send_otp_email(receiver_email,name, otp):
    try:
    
        email_content = f"""Hello {name},

Thank you for registering on Resume Analyzer. 
Your secure Email Verification OTP is: {otp}

Please use this code to complete your registration. Do not share this OTP with anyone.

Best regards,
Resume Analyzer Team"""

        msg = MIMEText(email_content)
        msg["Subject"] = "🎯 Verify Your Account - Resume Analyzer"
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email

        # For gimail SSL/TLs connection handel
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()  # Identify server
        server.starttls()  # On sequrity connection
        server.ehlo()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        # If mail send is fail 
        print("\n--- EMAIL SENDING ERROR LOG ---")
        print(e)
        print("--------------------------------\n")
        return False

# Routes and APIs

@app.route("/")
def home():
    return render_template("landing.html")

@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect(url_for("home"))
    return render_template("dashboard.html", name=session.get("user_name", "User"))

# ১. Sign-up Initiation and OTP Sending
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"message": "Please fill in all fields correctly."}), 400

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    existing_user = cursor.fetchone()
    conn.close()

    if existing_user:
        return jsonify({"message": "This email is already registered."}), 400

    # 4 digit Generate OTP
    otp = str(random.randint(1000, 9999))
    
    # Temporarily store user data in the session for verification
    TEMP_OTP_STORE[email] = {
        "name": name,
        "password": password,
        "otp": otp
    }

    if send_otp_email(email,name, otp):
        return jsonify({"message": "OTP has been sent to your email successfully."}), 200
    else:
        return jsonify({"message": "Failed to send the OTP email. Please check your email configuration."}), 500

# ২. Verify OTP and Create the Account
@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    user_otp = data.get("otp")
    email = data.get("email")  # Email sent from frontend

    # Reading data from global store
    temp_user = TEMP_OTP_STORE.get(email)

    if not temp_user:
        return jsonify({"message": "Verification session has expired or is invalid."}), 400

    if user_otp == temp_user['otp']:
        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (temp_user['name'], email, temp_user['password'])
            )
            conn.commit()
            conn.close()
            
            TEMP_OTP_STORE.pop(email, None) # Cleaning up data
            return jsonify({"message": "Account Created Successfully! Log In Now"}), 200
        except Exception as e:
            return jsonify({"message": f"Database Error: {str(e)}"}), 500
    else:
        return jsonify({"message": "Incorrect OTP! Please enter the correct code again."}), 400

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

    if file and file.filename.endswith(".pdf"):
        try:
            # Text extraction from PDF is supported.
            reader = PdfReader(file)
            resume_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    resume_text += text

            if not resume_text.strip():
                return jsonify({"message": "No text could be extracted from the PDF. The file may be scanned or image-based."}), 400

            # Giminni free API
            prompt = f"Analyze this resume carefully. Provide an ATS Score out of 100, brief feedback, strengths, and improvement areas. Resume text:\n\n{resume_text}"
            
            response = genai.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            
            analysis_result = response.text
            return jsonify({"message": "Success", "analysis": analysis_result})

        except Exception as e:
            print("Error:", e)
            return jsonify({"message": f"File Processing Error: {str(e)}"}), 500

    return jsonify({"message": "Only PDF files are allowed."}), 400

if __name__ == "__main__":
        import os
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port, debug=True)