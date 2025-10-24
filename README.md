🏥 Healthcare AI Assistant using LLM and Streamlit

An intelligent AI-powered healthcare assistant built using Large Language Models (LLMs) and Streamlit, designed to assist users with symptom checking, drug information lookup, medical translations, and health reminders.
The system provides an easy-to-use conversational interface that enables real-time medical guidance and information retrieval.

⚙️ Key Features

🤒 Symptom Checker – Analyzes user-entered symptoms and provides possible causes or health suggestions.

💊 Drug Checker – Fetches essential drug information, usage instructions, and side effects.

🧠 Translator – Translates medical information or prescriptions between multiple languages for better accessibility.

⏰ Health Reminder – Lets users schedule reminders for medication, appointments, or wellness tasks.

🗣️ LLM Integration – Uses a language model to understand natural language queries and provide contextual healthcare answers.

🌐 Streamlit Interface – Simple, clean, and interactive UI for real-time medical assistance.

🧩 Project Structure
pe/
├── app.py                     # Main Streamlit app entry point
├── requirements.txt           # Python dependencies
├── sampletext.txt             # Example text data
├── health_knowledge.json      # Knowledge base for symptom/drug information
└── tools/
    ├── symptom_checker.py     # Handles symptom input and health advice
    ├── drug_checker.py        # Provides drug details and side effects
    ├── translator.py          # Performs multilingual translation
    ├── reminder.py            # Reminder scheduling functionality
    └── reminder_tool.py       # Helper functions for reminders

🧠 Tech Stack
Category	Tools / Libraries
Frontend/UI	Streamlit
Backend/Logic	Python
Language Understanding	LLM API (e.g., OpenAI / Hugging Face)
Data Handling	pandas, json
Utilities	datetime, text processing, translation APIs
🚀 How to Run

Clone the repository

git clone https://github.com/your-username/healthcare-ai-assistant.git
cd healthcare-ai-assistant/pe


Install dependencies

pip install -r requirements.txt


Run the Streamlit app

streamlit run app.py


Open in your browser:
The app will launch automatically at http://localhost:8501
.

🧩 Example Use Cases
Feature	Example Query
Symptom Checker	“I have a sore throat and fever, what could it be?”
Drug Checker	“Tell me about Ibuprofen.”
Translator	“Translate this prescription to Hindi.”
Reminder	“Remind me to take my medicine at 9 PM.”
📦 Deliverables

Streamlit web app (app.py)

Modular tool scripts for each healthcare task

Health knowledge base (health_knowledge.json)

Requirements file for environment setup

Complete documentation and example usage

🔒 Disclaimer

This application is not a substitute for professional medical advice. It is an informational and educational tool. Always consult a qualified healthcare provider for medical concerns.
