# 📝 Aptitude \& Coding Test Platform

## 🚀 Overview

This project is a **full-stack web platform** that allows users to:

- 📝 Register and upload their resumes
- 🧠 Take **aptitude and coding tests**
- 📊 View personalized test scores on a user dashboard

**Admins can:**

- 👤 Manage users
- 📑 View test results
- 🛡️ Moderate tests and scores

The backend is built in **Python**, the frontend in **HTML, CSS, and JavaScript**, and **MongoDB** is used as the database.

***

## ✨ Features

### 👨‍💻 User Side

- 📝 **User Registration \& Login**
- 📄 **Resume Upload** during registration
- 🎯 **Aptitude Test** and 💻 **Coding Test** modules
- 📊 **Dashboard** showing user scores, progress, and details


### 🛠️ Admin Side

- 🔑 **Admin Login**
- 👥 **User Management** (view, edit, delete users)
- 📝 **Test Management** (add, update, remove tests)
- 📈 **Score Analytics Dashboard**


### 💻 Technology Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python (Flask/FastAPI/Django — specify your choice)
- **Database:** MongoDB (async or sync)
- **Authentication:** Session-based or JWT (specify if using)

***

## ⚙️ Installation

1. 🔄 **Clone the repository:**

```bash
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo
```

2. 🐍 **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

3. 📦 **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. 🗄️ **Create a .env file in the root folder with your MongoDB URI:**

```bash
MONGO_URI=your_mongodb_connection_string_here
```

5. ▶️ **Run the backend server:**

```bash
python app.py
```

6. 🌐 **Open the frontend in a browser (index.html) or run through a server if needed.**

***

## 🧑‍💻 Usage

- **Users:** Register → Upload Resume → Take Tests → View Dashboard
- **Admins:** Login → Manage Users → Monitor Test Results → Update Tests

***

## 🔒 Security Notes

- `.env` stores sensitive info like MongoDB URI and is never pushed to GitHub.
- Add `.env` to `.gitignore`.

***

## 🚀 Future Enhancements

- 🤖 Add ML-based resume analysis for better score prediction
- 📧 Email notifications to users
- 📊 Analytics charts for admins using Chart.js or similar

***

## 📄 License

🆓 Open-source project. Free to modify, use, and distribute.

***

If you need further tweaks or want specific emoji themes (tech, fun, etc.), just say the word, Sir!

