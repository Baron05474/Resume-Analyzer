Resume Analyzer

An AI-powered web application that analyzes resumes and provides **ATS score, strengths, feedback, and improvement suggestions** using Google's Gemini AI.

The application allows users to create an account with **email OTP verification**, log in securely, upload their resume in PDF format, and receive AI-generated insights about their resume.

---

 🚀 Features

* 🔐 User Registration & Login
* 📧 Email OTP Verification
* 🔑 Session-based Authentication
* 📄 PDF Resume Upload
* 🤖 AI-powered Resume Analysis using Google Gemini
* 📊 ATS Score out of 100
* 💡 Resume Feedback
* 💪 Strength Identification
* 🛠️ Improvement Suggestions
* 🗄️ SQLite Database for User Management
* 🚪 Logout Functionality
* 📱 Simple and User-Friendly Interface


 🖥️ How It Works

The application follows a simple workflow:

User
 │
 
Create Account
 │
 
Email OTP Verification
 │
 
Login
 │
 
Dashboard
 │
 
Upload Resume (PDF)
 │
 
Extract Resume Text
 │
 
Gemini AI Analysis
 │
 
ATS Score + Feedback + Suggestions


 🛠️ Technologies Used

 Backend

* Python
* Flask
* SQLite

## Frontend

* HTML
* CSS
* JavaScript

### AI & Resume Processing

* Google Gemini API
* `google-generativeai`
* `pypdf`

### Email Verification

* SMTP
* Brevo SMTP Relay
  
---
## 🔐 User Authentication

The application provides a basic authentication system.

### Sign Up

Users provide:

* Full Name
* Email
* Password

After registration, the application generates a **6-digit OTP** and attempts to send it to the user's email.

### OTP Verification

The user enters the received OTP.

If the OTP is correct, the account is created and stored in the SQLite database.

### Login

Registered users can log in using their email and password.

A Flask session is created after successful login.

---

## 📄 Resume Analysis

After logging in, users are redirected to the dashboard.

The user can:

1. Select a resume.
2. Upload the resume in PDF format.
3. Click **Check Resume**.
4. The application extracts text from the PDF.
5. The extracted text is sent to Gemini AI.
6. Gemini analyzes the resume.
7. The generated analysis is displayed on the dashboard.

The AI is instructed to provide:

* **ATS Score out of 100**
* Resume feedback
* Strengths
* Areas for improvement

---

## 🤖 AI Analysis

The project uses Google's Gemini model to analyze the extracted resume content.

The application sends a prompt containing the resume text and requests an analysis focused on ATS performance, strengths, and areas for improvement.

This makes the application useful for users who want an initial AI-powered review of their resume before applying for jobs or internships.

---
## Screenshots

### 1. Login Page
![Login Page](assets/login.png)

### 2. Sign Up Page
![Sign Up Page](assets/signup.png)

### 3. OTP Verification Page
![OTP Verification](assets/otp.png)

### 4. Dashboard
![Dashboard](assets/dashboard.png)


## 🎯 Project Purpose

The main goal of this project is to build a simple and practical **AI-powered Resume Analyzer** that helps students and job seekers understand the strengths and weaknesses of their resumes.

It also demonstrates the integration of:

* Web development
* Backend development
* Database management
* PDF processing
* Email verification
* REST-style API routes
* Generative AI

into a single full-stack application.

---

## 👨‍💻 Author

**Baron Bhowmick**

B.Tech in Computer Science & Engineering




