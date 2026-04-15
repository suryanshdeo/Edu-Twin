# EduTwin

Hi! This is EduTwin - a project where we try to build a "digital twin" of a student and use it to give more personal learning support.

The core idea is simple: instead of one-size-fits-all learning, we keep a live profile of how a student is doing, then use that profile to generate better help.

## What this project does right now

- login/signup for students
- stores student details in SQLite
- builds a Live Learner Profile (LLP)
- finds likely weak topics
- gives personalized explanations
- predicts performance level
- simulates exam-style answers

## Stack

- Python
- Streamlit
- SQLite
- Groq API (LLM)

## Folder layout

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

## Run locally

```bash
git clone https://github.com/suryanshdeo/Edu-Twin.git
cd EduTwin
python -m venv venv
```

Activate venv:

- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

Install deps:

```bash
pip install -r requirements.txt
```

Create `.env` in project root:

```env
GROQ_API_KEY=your_api_key_here
```

Start app:

```bash
streamlit run ui/app.py
```

## Typical student flow

1. Sign up / log in
2. Fill profile inputs
3. LLP gets created or updated
4. Use diagnosis, explanation, prediction, and simulation features

## Notes

- passwords are hashed before storing
- keep API keys in `.env` only
- this project is still evolving, so expect changes
