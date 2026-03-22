# 🎓 EduTwin: LLM-Powered Digital Twin of University Students

## 🚀 Overview

EduTwin is an AI-powered system that creates a **Digital Twin of a student** using a dynamic **Live Learner Profile (LLP)** built from real user data.
It leverages Large Language Models (LLMs) to simulate student behavior, diagnose weaknesses, predict performance, and generate personalized learning content.

---

## 💡 Problem Statement

Most education systems treat students uniformly despite differences in:

* Learning pace
* Background knowledge
* Study habits
* Cognitive preferences

EduTwin addresses this by building a **personalized AI twin for each student**, enabling adaptive and intelligent learning.

---

## 🧠 Key Features

### 🔐 Authentication System

* Secure **login/signup**
* Password hashing and session handling

### 🗄️ Database-Driven Profiles

* Stores real student data (no synthetic data)
* Persistent and updatable learner profiles

### 📊 Live Learner Profile (LLP)

* Dynamic representation of student state
* Includes academic, behavioral, and self-reported data

### 🔍 Weakness Diagnosis

* Identifies weak topics using LLM reasoning

### 📘 Personalized Explanations

* Tailored explanations based on student profile

### 📈 Performance Prediction

* Predicts future performance (High / Medium / Low)

### 📝 Exam Answer Simulation

* Simulates how a student would answer exam questions

---

## 🏗️ Project Structure

```id="9u0bmn"
EduTwin/
├── data/
│   ├── generate_data.py
│   └── raw/
├── core/
│   ├── profile_builder.py
│   └── llp_updater.py
├── twin/
│   ├── prompt_engine.py
│   ├── weakness_diagnoser.py
│   ├── explainer.py
│   ├── predictor.py
│   ├── exam_simulator.py
│   └── twin_engine.py
├── database/
│   ├── db.py
│   └── crud.py
├── auth/
│   └── auth.py
├── ui/
│   ├── app.py
│   └── views/
│       ├── student_view.py
│       ├── teacher_view.py
│       └── profile_form.py
├── setup.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Tech Stack

* **LLM**: Groq API
* **Backend**: Python
* **Frontend/UI**: Streamlit
* **Database**: SQLite
* **Auth**: Custom authentication with hashed passwords

---

## 🔄 System Workflow

1. **User Authentication**

   * Student signs up / logs in

2. **Profile Creation**

   * Student inputs:

     * Academic scores
     * Study habits
     * Confidence levels

3. **Database Storage**

   * Data stored and managed via CRUD operations

4. **LLP Generation**

   * Profile Builder creates structured learner profile

5. **LLM Twin Engine**

   * Uses LLP for:

     * Weakness detection
     * Explanation generation
     * Prediction
     * Simulation

---

## 🛠️ Installation & Setup

### 1️⃣ Clone Repository

```bash id="v0bch8"
git clone https://github.com/YOUR_USERNAME/EduTwin.git
cd EduTwin
```

---

### 2️⃣ Create Virtual Environment

```bash id="uv6v0z"
python -m venv venv
```

Activate:

* Windows:

```bash id="0jhv02"
venv\Scripts\activate
```

* Mac/Linux:

```bash id="vt4q8z"
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```bash id="17lq6d"
pip install -r requirements.txt
```

---

### 4️⃣ Setup Environment Variables

Create a `.env` file:

```id="l9ehts"
GROQ_API_KEY=your_api_key_here
```

---

### 5️⃣ Run the Application

```bash id="3gpytr"
streamlit run ui/app.py
```

---

## 👨‍🎓 Usage

### Student Flow

* Sign up / Log in
* Fill profile form
* Generate learner profile
* Use:

  * Weakness diagnosis
  * Topic explanation
  * Performance prediction
  * Exam simulation

---

### Teacher Flow 

* View all students
* Analyze class trends
* Identify weak learners

---

## 📈 Evaluation Metrics

| Capability         | Metric                |
| ------------------ | --------------------- |
| Weakness Diagnosis | Precision / Recall    |
| Prediction         | Accuracy / F1         |
| Explanation        | Human Rating          |
| Simulation         | Behavioral Similarity |

---

## 🔐 Security Practices

* Password hashing (bcrypt)
* Environment variable usage for API keys
* No sensitive data stored in repo

---

## 🔮 Future Enhancements

* 📅 Temporal tracking of student progress
* 🔁 Counterfactual analysis
* 👥 Student clustering
* 🌐 Deployment (Streamlit Cloud)
* 📊 Advanced analytics dashboard

---







