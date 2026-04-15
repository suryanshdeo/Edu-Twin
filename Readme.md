# EduTwin

EduTwin is an AI-powered learning companion that builds a **digital twin** of each student from real profile data.  
It helps students learn better with personalized explanations, weakness insights, performance predictions, and exam-style response simulation.

## Why EduTwin?

Every student learns differently. Most systems still teach everyone the same way.

EduTwin aims to solve that by combining:

- student profile data
- a dynamic Live Learner Profile (LLP)
- LLM-based reasoning for adaptive support

## What it can do

- Student signup/login with hashed passwords
- Store and update student data in SQLite
- Build and update a Live Learner Profile (LLP)
- Diagnose weak areas
- Generate personalized explanations
- Predict likely performance bands
- Simulate exam answers in a student-specific style

## Tech stack

- **Backend:** Python
- **UI:** Streamlit
- **Database:** SQLite
- **LLM:** Groq API
- **Auth:** Custom auth + password hashing

## Project structure

```text
EduTwin/
├── auth/
├── core/
├── data/
├── database/
├── twin/
├── ui/
├── requirements.txt
├── setup.py
└── Readme.md
```

## Quick start

### 1. Clone the repo

```bash
git clone https://github.com/suryanshdeo/Edu-Twin.git
cd EduTwin
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

**Windows**

```bash
venv\Scripts\activate
```

**macOS/Linux**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_api_key_here
```

### 5. Run the app

```bash
streamlit run ui/app.py
```

## Typical flow

1. Student logs in
2. Student fills profile information
3. LLP is generated/updated
4. Twin engine provides diagnosis, explanation, prediction, and simulation

## Security notes

- Passwords are hashed before storage
- API keys are loaded from environment variables
- No secrets should be committed to this repository

## Roadmap ideas

- Progress tracking over time
- Better class-level analytics for teachers
- More explainability in predictions
- Cloud deployment support
